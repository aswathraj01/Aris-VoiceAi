import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
from vosk import KaldiRecognizer, Model, SetLogLevel

SetLogLevel(-1)
SAMPLE_RATE = 16000
active_sample_rate = SAMPLE_RATE
BLOCK_SIZE = 4000
COMMAND_TIMEOUT = 9.0
CONVERSATION_TIMEOUT_OPTIONS = {10, 15, 20}
DEFAULT_CONVERSATION_TIMEOUT = 15
conversation_timeout_seconds = DEFAULT_CONVERSATION_TIMEOUT
conversation_active = False
last_voice_activity_at = 0.0
WAKE_GRAMMAR = json.dumps(["aries", "hey aries", "iris", "hey iris", "irish", "hey irish", "aris", "hey aris", "[unk]"])
WAKE_ACKNOWLEDGMENT = "Mm-hmm."
DEBUG_MODE = os.environ.get("ARIS_DEBUG") == "1"
MAX_WAKE_BUFFER_BLOCKS = 64
AUDIO_QUEUE = queue.Queue(maxsize=48)
COMMAND_QUEUE = queue.Queue()
model = None
recognizer = None
stream = None
is_listening = False
mode = "idle"
armed = False
command_started_at = 0.0
completed_segments = []
selected_input_device_id = ""
selected_output_device_id = ""
wake_audio_buffer = []


def send(kind, **values):
    message = {"type": kind}
    message.update(values)
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def read_commands():
    for line in sys.stdin:
        try:
            COMMAND_QUEUE.put(json.loads(line))
        except (json.JSONDecodeError, TypeError):
            send("error", message="Voice worker received an invalid control message.")


def enumerate_devices():
    raw_devices = sd.query_devices()
    host_apis = sd.query_hostapis()
    defaults = sd.default.device
    default_ids = {"input": "", "output": ""}
    devices = {"inputs": [], "outputs": []}
    occurrences = {}

    for index, raw in enumerate(raw_devices):
        host_api = host_apis[int(raw["hostapi"])]["name"]
        name = str(raw["name"])
        base = json.dumps([host_api, name], ensure_ascii=False, separators=(",", ":"))
        ordinal = occurrences.get(base, 0)
        occurrences[base] = ordinal + 1
        device_id = base + "#" + str(ordinal)
        device = {
            "id": device_id,
            "name": name,
            "hostApi": host_api,
            "maxInputChannels": int(raw["max_input_channels"]),
            "maxOutputChannels": int(raw["max_output_channels"]),
            "defaultSampleRate": int(round(float(raw["default_samplerate"]))),
        }
        if device["maxInputChannels"] > 0:
            devices["inputs"].append(device)
            if defaults[0] is not None and index == int(defaults[0]):
                default_ids["input"] = device_id
        if device["maxOutputChannels"] > 0:
            devices["outputs"].append(device)
            if defaults[1] is not None and index == int(defaults[1]):
                default_ids["output"] = device_id

    return {**devices, "defaultInputId": default_ids["input"], "defaultOutputId": default_ids["output"]}


def resolve_device_id(device_id, direction):
    if not device_id:
        return None
    for device in enumerate_devices()[direction]:
        if device["id"] != device_id:
            continue
        raw_devices = sd.query_devices()
        host_apis = sd.query_hostapis()
        for index, raw in enumerate(raw_devices):
            host_api = host_apis[int(raw["hostapi"])]["name"]
            if raw["name"] == device["name"] and host_api == device["hostApi"]:
                count = sum(1 for prior in raw_devices[:index] if prior["name"] == raw["name"] and host_apis[int(prior["hostapi"])]["name"] == host_api)
                if device_id.endswith("#" + str(count)):
                    return index
    raise RuntimeError("The selected audio device is no longer available.")


def choose_input_sample_rate(device):
    info = sd.query_devices(device, "input")
    native_rate = int(round(float(info["default_samplerate"])))
    candidates = list(dict.fromkeys([SAMPLE_RATE, native_rate, 48000, 44100, 32000, 24000, 22050]))
    failures = []
    for rate in candidates:
        try:
            sd.check_input_settings(device=device, channels=1, dtype="int16", samplerate=rate)
            return rate
        except Exception as exc:
            failures.append(str(exc))
    reason = failures[-1] if failures else "No candidate sample rates were available."
    raise RuntimeError("Microphone '" + str(info["name"]) + "' does not support ARIS input formats. Tried " + ", ".join(str(rate) for rate in candidates) + " Hz. " + reason)


def list_devices_cli():
    try:
        sys.stdout.write(json.dumps(enumerate_devices(), ensure_ascii=False) + "\n")
        return 0
    except Exception as exc:
        sys.stderr.write(type(exc).__name__ + "\n")
        return 2


def audio_callback(indata, frames, timing, status):
    if status:
        pass
    data = bytes(indata)
    try:
        AUDIO_QUEUE.put_nowait(data)
    except queue.Full:
        try:
            AUDIO_QUEUE.get_nowait()
            AUDIO_QUEUE.put_nowait(data)
        except queue.Empty:
            pass


def make_recognizer(wake=False):
    instance = KaldiRecognizer(model, active_sample_rate, WAKE_GRAMMAR) if wake else KaldiRecognizer(model, active_sample_rate)
    instance.SetWords(False)
    return instance


def clear_audio_queue():
    while not AUDIO_QUEUE.empty():
        try:
            AUDIO_QUEUE.get_nowait()
        except queue.Empty:
            break


def close_input_stream():
    global stream, is_listening
    if stream is not None:
        try:
            stream.stop()
        finally:
            stream.close()
            stream = None
    is_listening = False


def open_input_stream():
    global stream, is_listening, active_sample_rate
    device = resolve_device_id(selected_input_device_id, "inputs")
    active_sample_rate = choose_input_sample_rate(device)
    stream = sd.RawInputStream(
        samplerate=active_sample_rate, blocksize=BLOCK_SIZE, device=device, channels=1,
        dtype="int16", callback=audio_callback,
    )
    stream.start()
    is_listening = True


def begin_wake_monitoring():
    global recognizer, mode, wake_audio_buffer
    if not armed or mode == "awaiting":
        return
    close_input_stream()
    clear_audio_queue()
    wake_audio_buffer = []
    recognizer = make_recognizer(wake=True)
    open_input_stream()
    mode = "wake"
    send("armed", sampleRate=active_sample_rate)


def begin_command_capture(conversation=False):
    global recognizer, mode, command_started_at, last_voice_activity_at
    close_input_stream()
    clear_audio_queue()
    recognizer = make_recognizer()
    command_started_at = time.monotonic()
    mode = "conversation" if conversation else "command"
    last_voice_activity_at = time.monotonic()
    open_input_stream()
    send("listening")


def start_conversation():
    global conversation_active
    conversation_active = True
    send("conversation_started", timeoutSeconds=conversation_timeout_seconds)


def end_conversation():
    global conversation_active, recognizer, mode, wake_audio_buffer
    close_input_stream()
    clear_audio_queue()
    recognizer = None
    wake_audio_buffer = []
    mode = "idle"
    conversation_active = False
    send("conversation_ended", timeoutSeconds=conversation_timeout_seconds)
    if armed:
        try:
            begin_wake_monitoring()
        except Exception as exc:
            armed = False
            send("error", message="Wake listener could not restart after conversation: " + type(exc).__name__ + ": " + str(exc)[:240])


def acknowledge_and_listen():
    global mode, recognizer
    close_input_stream()
    clear_audio_queue()
    recognizer = None
    mode = "awaiting"
    send("acknowledging")
    start_conversation()
    try:
        speak_text(WAKE_ACKNOWLEDGMENT)
    except Exception as exc:
        sys.stderr.write("Wake acknowledgment failed: " + type(exc).__name__ + ": " + str(exc) + "\n")
        sys.stderr.flush()
    begin_command_capture(conversation=True)


def wake_tail(text):
    words = [word for word in str(text or "").lower().split() if word != "[unk]"]
    names = {"aris", "eris", "aries", "iris", "irish"}
    if len(words) >= 2 and words[0] == "hey" and words[1] in names:
        return " ".join(words[2:])
    if words and words[0] in names:
        return " ".join(words[1:])
    if len(words) >= 2 and words[0] == "here" and words[1] == "is":
        return " ".join(words[2:])
    if len(words) >= 2 and words[0] == "here's" and words[1] in names:
        return " ".join(words[2:])
    return None


def transcribe_audio(audio_blocks):
    command_recognizer = make_recognizer()
    for block in audio_blocks:
        command_recognizer.AcceptWaveform(block)
    result = json.loads(command_recognizer.FinalResult())
    return result.get("text", "").strip()


def finish_command(text):
    global recognizer, mode
    close_input_stream()
    clear_audio_queue()
    recognizer = None
    mode = "awaiting"
    send("transcript", text=str(text or "").strip())


def process_audio():
    global recognizer, wake_audio_buffer, mode, armed, last_voice_activity_at
    try:
        audio = AUDIO_QUEUE.get_nowait()
    except queue.Empty:
        if mode == "conversation" and time.monotonic() - last_voice_activity_at >= conversation_timeout_seconds:
            end_conversation()
        elif mode == "command" and time.monotonic() - command_started_at > COMMAND_TIMEOUT:
            finish_command("")
        return

    try:
        if mode == "conversation" and np.sqrt(np.mean(np.frombuffer(audio, dtype=np.int16).astype(np.float32) ** 2)) >= 650:
            last_voice_activity_at = time.monotonic()
        if mode == "wake":
            wake_audio_buffer.append(audio)
            if len(wake_audio_buffer) > MAX_WAKE_BUFFER_BLOCKS:
                del wake_audio_buffer[0]
        if not recognizer.AcceptWaveform(audio):
            return
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip()
        if mode == "wake":
            tail = wake_tail(text)
            if tail is None:
                wake_audio_buffer = []
                return
            full_text = transcribe_audio(wake_audio_buffer)
            full_tail = wake_tail(full_text)
            wake_audio_buffer = []
            start_conversation()
            if full_tail:
                finish_command(full_tail)
            else:
                acknowledge_and_listen()
        elif mode in {"command", "conversation"}:
            if text:
                finish_command(text)
            elif time.monotonic() - command_started_at > COMMAND_TIMEOUT:
                finish_command("")
    except Exception as exc:
        close_input_stream()
        clear_audio_queue()
        recognizer = None
        mode = "idle"
        armed = False
        if DEBUG_MODE:
            import traceback
            traceback.print_exc(file=sys.stderr)
        send("error", message="Speech recognition stopped after an audio error: " + type(exc).__name__ + ": " + str(exc)[:240])


def speak_text(text):
    output_device = resolve_device_id(selected_output_device_id, "outputs") if selected_output_device_id else None
    script_path = Path(__file__).resolve().with_name("synthesize.ps1")
    if not script_path.is_file():
        raise RuntimeError("Windows speech synthesis script is missing: " + str(script_path))
    with tempfile.TemporaryDirectory(prefix="aris-speech-") as temp_dir:
        wav_path = Path(temp_dir) / "speech.wav"
        command = [
            "powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-STA",
            "-ExecutionPolicy", "Bypass", "-File", str(script_path), str(wav_path), str(text)[:1600],
        ]
        try:
            result = subprocess.run(
                command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Windows speech synthesis timed out after 20 seconds.") from exc
        if result.returncode != 0:
            reason = (result.stderr or result.stdout or "Windows speech synthesis failed.").strip()
            raise RuntimeError(reason[-600:])
        with wave.open(str(wav_path), "rb") as audio:
            if audio.getcomptype() != "NONE" or audio.getsampwidth() != 2:
                raise RuntimeError("Windows speech synthesizer produced an unsupported audio format.")
            channels = audio.getnchannels()
            sample_rate = audio.getframerate()
            samples = np.frombuffer(audio.readframes(audio.getnframes()), dtype=np.int16)
            if channels > 1:
                samples = samples.reshape((-1, channels))
            sd.play(samples, samplerate=sample_rate, device=output_device, blocking=True)


def main():
    global model, armed, mode, selected_input_device_id, selected_output_device_id, conversation_timeout_seconds, conversation_active
    model_path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path("")
    if not model_path.is_dir():
        send("error", message="Offline speech model is missing at " + str(model_path) + ". Run the voice setup instructions.")
        return 2

    try:
        model = Model(str(model_path))
    except Exception as exc:
        if DEBUG_MODE:
            import traceback
            traceback.print_exc(file=sys.stderr)
        send("error", message="Voice engine could not start: " + type(exc).__name__ + ": " + str(exc)[:240])
        return 2

    threading.Thread(target=read_commands, daemon=True).start()
    send("ready")

    while True:
        command = None
        try:
            command = COMMAND_QUEUE.get(timeout=0.02)
        except queue.Empty:
            pass

        if is_listening and mode in {"wake", "command", "conversation"}:
            process_audio()
        if command is None:
            continue

        action = command.get("action")
        if action == "configure_audio":
            previous_input = selected_input_device_id
            selected_input_device_id = str(command.get("inputDeviceId") or "")[:500]
            selected_output_device_id = str(command.get("outputDeviceId") or "")[:500]
            requested_timeout = int(command.get("conversationTimeoutSeconds", DEFAULT_CONVERSATION_TIMEOUT))
            conversation_timeout_seconds = requested_timeout if requested_timeout in CONVERSATION_TIMEOUT_OPTIONS else DEFAULT_CONVERSATION_TIMEOUT
            send("audio_configured")
            if mode == "wake" and previous_input != selected_input_device_id:
                begin_wake_monitoring()
            elif mode == "conversation" and previous_input != selected_input_device_id:
                begin_command_capture(conversation=True)
        elif action == "arm_wake":
            armed = True
            if mode != "awaiting":
                try:
                    begin_wake_monitoring()
                except Exception as exc:
                    armed = False
                    mode = "idle"
                    close_input_stream()
                    if DEBUG_MODE:
                        import traceback
                        traceback.print_exc(file=sys.stderr)
                    send("error", message="Microphone could not start: " + type(exc).__name__ + ": " + str(exc)[:240])
        elif action == "disarm":
            armed = False
            close_input_stream()
            clear_audio_queue()
            recognizer = None
            mode = "idle"
            conversation_active = False
            send("disarmed")
        elif action == "cancel_command":
            if mode in {"command", "conversation"}:
                close_input_stream()
                clear_audio_queue()
                recognizer = None
                mode = "idle"
                if armed:
                    try:
                        if conversation_active:
                            begin_command_capture(conversation=True)
                        else:
                            begin_wake_monitoring()
                    except Exception as exc:
                        armed = False
                        if DEBUG_MODE:
                            import traceback
                            traceback.print_exc(file=sys.stderr)
                        send("error", message="Microphone could not restart: " + type(exc).__name__ + ": " + str(exc)[:240])
                else:
                    send("disarmed")
        elif action == "resume_conversation":
            if armed and conversation_active and mode in {"awaiting", "idle", "wake"}:
                try:
                    begin_command_capture(conversation=True)
                except Exception as exc:
                    if DEBUG_MODE:
                        import traceback
                        traceback.print_exc(file=sys.stderr)
                    send("error", message="Conversation microphone could not restart: " + type(exc).__name__ + ": " + str(exc)[:240])
        elif action == "resume_wake":
            if armed and mode == "awaiting":
                mode = "idle"
            if armed and mode == "idle":
                try:
                    begin_wake_monitoring()
                except Exception as exc:
                    armed = False
                    if DEBUG_MODE:
                        import traceback
                        traceback.print_exc(file=sys.stderr)
                    send("error", message="Microphone could not restart: " + type(exc).__name__ + ": " + str(exc)[:240])
        elif action == "speak":
            text = str(command.get("text", "")).strip()
            if text:
                close_input_stream()
                clear_audio_queue()
                recognizer = None
                mode = "awaiting" if armed else "idle"
                try:
                    speak_text(text[:1600])
                    send("spoken")
                    if armed:
                        mode = "idle"
                        if conversation_active:
                            begin_command_capture(conversation=True)
                        else:
                            begin_wake_monitoring()
                except Exception as exc:
                    mode = "idle"
                    if DEBUG_MODE:
                        import traceback
                        traceback.print_exc(file=sys.stderr)
                    send("error", message="Speech output failed: " + type(exc).__name__ + ": " + str(exc)[:240])
                    if armed:
                        try:
                            if conversation_active:
                                begin_command_capture(conversation=True)
                            else:
                                begin_wake_monitoring()
                        except Exception:
                            armed = False
        elif action == "shutdown":
            armed = False
            conversation_active = False
            close_input_stream()
            clear_audio_queue()
            return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list-devices":
        raise SystemExit(list_devices_cli())
    raise SystemExit(main())

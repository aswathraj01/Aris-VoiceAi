import json
import os
import queue
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path

import numpy as np
import pyttsx3
import sounddevice as sd
from vosk import KaldiRecognizer, Model, SetLogLevel

SetLogLevel(-1)
SAMPLE_RATE = 16000
BLOCK_SIZE = 4000
COMMAND_TIMEOUT = 9.0
WAKE_GRAMMAR = json.dumps(["aries", "hey aries", "[unk]"])
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
speech_engine = None
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
    instance = KaldiRecognizer(model, SAMPLE_RATE, WAKE_GRAMMAR) if wake else KaldiRecognizer(model, SAMPLE_RATE)
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
    global stream, is_listening
    device = resolve_device_id(selected_input_device_id, "inputs")
    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, device=device, channels=1,
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
    send("armed")


def begin_command_capture():
    global recognizer, mode, command_started_at
    clear_audio_queue()
    recognizer = make_recognizer()
    command_started_at = time.monotonic()
    mode = "command"
    send("listening")


def wake_tail(text):
    words = [word for word in str(text or "").lower().split() if word != "[unk]"]
    names = {"aris", "eris", "aries"}
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
    global recognizer, wake_audio_buffer, mode, armed
    try:
        audio = AUDIO_QUEUE.get_nowait()
    except queue.Empty:
        if mode == "command" and time.monotonic() - command_started_at > COMMAND_TIMEOUT:
            finish_command("")
        return

    try:
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
            if full_tail:
                finish_command(full_tail)
            else:
                begin_command_capture()
        elif mode == "command":
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
        send("error", message="Speech recognition stopped after an audio error: " + type(exc).__name__)


def speak_text(text):
    if not selected_output_device_id:
        speech_engine.say(text)
        speech_engine.runAndWait()
        return

    output_device = resolve_device_id(selected_output_device_id, "outputs")
    with tempfile.TemporaryDirectory(prefix="aris-speech-") as temp_dir:
        wav_path = Path(temp_dir) / "speech.wav"
        speech_engine.save_to_file(text, str(wav_path))
        speech_engine.runAndWait()
        with wave.open(str(wav_path), "rb") as audio:
            if audio.getcomptype() != "NONE" or audio.getsampwidth() != 2:
                raise RuntimeError("Speech engine produced an unsupported audio format.")
            channels = audio.getnchannels()
            sample_rate = audio.getframerate()
            samples = np.frombuffer(audio.readframes(audio.getnframes()), dtype=np.int16)
            if channels > 1:
                samples = samples.reshape((-1, channels))
            sd.play(samples, samplerate=sample_rate, device=output_device, blocking=True)


def main():
    global model, speech_engine, armed, mode, selected_input_device_id, selected_output_device_id
    model_path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path("")
    if not model_path.is_dir():
        send("error", message="Offline speech model is missing. Run the voice setup instructions.")
        return 2

    try:
        model = Model(str(model_path))
        speech_engine = pyttsx3.init()
        speech_engine.setProperty("rate", 165)
    except Exception as exc:
        send("error", message="Voice engine could not start: " + type(exc).__name__)
        return 2

    threading.Thread(target=read_commands, daemon=True).start()
    send("ready")

    while True:
        command = None
        try:
            command = COMMAND_QUEUE.get(timeout=0.02)
        except queue.Empty:
            pass

        if is_listening and mode in {"wake", "command"}:
            process_audio()
        if command is None:
            continue

        action = command.get("action")
        if action == "configure_audio":
            previous_input = selected_input_device_id
            selected_input_device_id = str(command.get("inputDeviceId") or "")[:500]
            selected_output_device_id = str(command.get("outputDeviceId") or "")[:500]
            send("audio_configured")
            if mode == "wake" and previous_input != selected_input_device_id:
                begin_wake_monitoring()
        elif action == "arm_wake":
            armed = True
            if mode != "awaiting":
                try:
                    begin_wake_monitoring()
                except Exception as exc:
                    armed = False
                    mode = "idle"
                    close_input_stream()
                    send("error", message="Microphone could not start: " + type(exc).__name__)
        elif action == "disarm":
            armed = False
            close_input_stream()
            clear_audio_queue()
            recognizer = None
            mode = "idle"
            send("disarmed")
        elif action == "cancel_command":
            if mode == "command":
                close_input_stream()
                clear_audio_queue()
                recognizer = None
                mode = "idle"
                if armed:
                    try:
                        begin_wake_monitoring()
                    except Exception as exc:
                        armed = False
                        send("error", message="Microphone could not restart: " + type(exc).__name__)
                else:
                    send("disarmed")
        elif action == "resume_wake":
            if armed and mode == "awaiting":
                mode = "idle"
            if armed and mode == "idle":
                try:
                    begin_wake_monitoring()
                except Exception as exc:
                    armed = False
                    send("error", message="Microphone could not restart: " + type(exc).__name__)
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
                        begin_wake_monitoring()
                except Exception as exc:
                    mode = "idle"
                    send("error", message="Speech output failed: " + type(exc).__name__)
                    if armed:
                        try:
                            begin_wake_monitoring()
                        except Exception:
                            armed = False
        elif action == "shutdown":
            armed = False
            close_input_stream()
            clear_audio_queue()
            if speech_engine is not None:
                try:
                    speech_engine.stop()
                except Exception:
                    pass
            return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list-devices":
        raise SystemExit(list_devices_cli())
    raise SystemExit(main())

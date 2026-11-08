import json
import os
import queue
import sys
import threading
import tempfile
import wave
from pathlib import Path

import numpy as np
import pyttsx3
import sounddevice as sd
from vosk import KaldiRecognizer, Model, SetLogLevel

SetLogLevel(-1)
SAMPLE_RATE = 16000
BLOCK_SIZE = 4000
AUDIO_QUEUE = queue.Queue(maxsize=48)
COMMAND_QUEUE = queue.Queue()
model = None
recognizer = None
stream = None
is_listening = False
completed_segments = []
speech_engine = None
selected_input_device_id = ""
selected_output_device_id = ""


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
    devices = enumerate_devices()[direction]
    for device in devices:
        if device["id"] == device_id:
            raw_devices = sd.query_devices()
            host_apis = sd.query_hostapis()
            for index, raw in enumerate(raw_devices):
                host_api = host_apis[int(raw["hostapi"])]["name"]
                if raw["name"] == device["name"] and host_api == device["hostApi"]:
                    # IDs include duplicate ordinal; compare by enumeration order.
                    count = sum(1 for prior in raw_devices[:index] if prior["name"] == raw["name"] and host_apis[int(prior["hostapi"])]["name"] == host_api)
                    if device["id"].endswith("#" + str(count)):
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
        # Device status details are intentionally not logged.
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


def begin_capture():
    global recognizer, stream, is_listening, completed_segments
    while not AUDIO_QUEUE.empty():
        try:
            AUDIO_QUEUE.get_nowait()
        except queue.Empty:
            break
    completed_segments = []
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    recognizer.SetWords(False)
    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        device=resolve_device_id(selected_input_device_id, "inputs"),
        channels=1,
        dtype="int16",
        callback=audio_callback,
    )
    stream.start()
    is_listening = True
    send("listening")


def finish_capture():
    global stream, is_listening, recognizer, completed_segments
    if stream is not None:
        stream.stop()
        stream.close()
        stream = None
    is_listening = False
    if recognizer is not None:
        try:
            while True:
                try:
                    audio = AUDIO_QUEUE.get_nowait()
                except queue.Empty:
                    break
                if recognizer.AcceptWaveform(audio):
                    result = json.loads(recognizer.Result())
                    segment = result.get("text", "").strip()
                    if segment:
                        completed_segments.append(segment)
            result = json.loads(recognizer.FinalResult())
            final_text = result.get("text", "").strip()
            if final_text:
                completed_segments.append(final_text)
        except (json.JSONDecodeError, RuntimeError):
            pass
    text = " ".join(part for part in completed_segments if part).strip()
    recognizer = None
    completed_segments = []
    send("transcript", text=text)


def main():
    global model, speech_engine, is_listening, selected_input_device_id, selected_output_device_id
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

        if is_listening and recognizer is not None:
            try:
                audio = AUDIO_QUEUE.get_nowait()
                if recognizer.AcceptWaveform(audio):
                    result = json.loads(recognizer.Result())
                    segment = result.get("text", "").strip()
                    if segment:
                        completed_segments.append(segment)
            except queue.Empty:
                pass
            except (json.JSONDecodeError, RuntimeError):
                send("error", message="Speech recognition encountered an audio error.")

        if command is None:
            continue
        action = command.get("action")
        if action == "start" and not is_listening:
            try:
                begin_capture()
            except Exception as exc:
                is_listening = False
                send("error", message=(str(exc) if isinstance(exc, RuntimeError) else "Microphone could not start: " + type(exc).__name__))
        elif action == "stop" and is_listening:
            try:
                finish_capture()
            except Exception as exc:
                is_listening = False
                send("error", message="Microphone could not stop: " + type(exc).__name__)
        elif action == "configure_audio":
            selected_input_device_id = str(command.get("inputDeviceId") or "")[:500]
            selected_output_device_id = str(command.get("outputDeviceId") or "")[:500]
            send("audio_configured")
        elif action == "speak":
            text = str(command.get("text", "")).strip()
            if text:
                try:
                    speak_text(text[:1600])
                    send("spoken")
                except Exception as exc:
                    send("error", message="Speech output failed: " + type(exc).__name__)
        elif action == "shutdown":
            if is_listening:
                try:
                    finish_capture()
                except Exception:
                    pass
            if speech_engine is not None:
                try:
                    speech_engine.stop()
                except Exception:
                    pass
            return 0


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


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list-devices":
        raise SystemExit(list_devices_cli())
    raise SystemExit(main())

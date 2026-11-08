import json
import os
import queue
import sys
import threading
from pathlib import Path

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
        device=None,
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
    global model, speech_engine, is_listening
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
                send("error", message="Microphone could not start: " + type(exc).__name__)
        elif action == "stop" and is_listening:
            try:
                finish_capture()
            except Exception as exc:
                is_listening = False
                send("error", message="Microphone could not stop: " + type(exc).__name__)
        elif action == "speak":
            text = str(command.get("text", "")).strip()
            if text:
                try:
                    speech_engine.say(text[:1600])
                    speech_engine.runAndWait()
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


if __name__ == "__main__":
    raise SystemExit(main())

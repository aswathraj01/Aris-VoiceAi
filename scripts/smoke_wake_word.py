import importlib.util
import json
import os
import tempfile
import wave
from pathlib import Path

import pyttsx3
from vosk import KaldiRecognizer, Model, SetLogLevel

SetLogLevel(-1)
root = Path(__file__).resolve().parents[1]
model_path = Path(os.environ.get("LOCALAPPDATA", "")) / "ARIS" / "models" / "vosk-model-small-en-in-0.4"
if not (model_path / "am").is_dir():
    raise SystemExit("Offline speech model is not installed.")

spec = importlib.util.spec_from_file_location("aris_voice_worker", root / "voice" / "worker.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
phrase = "Hey Iris, open Chrome."
if worker.WAKE_ACKNOWLEDGMENT != "Mm-hmm." or worker.wake_tail("Iris") != "" or worker.wake_tail("Hey Iris") != "":
    raise SystemExit("The wake acknowledgment or wake-only parsing is not configured.")
with tempfile.TemporaryDirectory(prefix="aris-wake-check-") as folder:
    audio_path = Path(folder) / "wake.wav"
    engine = pyttsx3.init()
    engine.save_to_file(phrase, str(audio_path))
    engine.runAndWait()
    engine.stop()
    model = Model(str(model_path))
    with wave.open(str(audio_path), "rb") as audio:
        audio_bytes = audio.readframes(audio.getnframes())
        sample_rate = audio.getframerate()
        wake_recognizer = KaldiRecognizer(model, sample_rate, worker.WAKE_GRAMMAR)
        for offset in range(0, len(audio_bytes), 8000):
            wake_recognizer.AcceptWaveform(audio_bytes[offset:offset + 8000])
        wake_text = json.loads(wake_recognizer.FinalResult()).get("text", "")
        if worker.wake_tail(wake_text) is None:
            raise SystemExit("The offline model did not detect the configured ARIS wake phrase: " + wake_text)

        command_recognizer = KaldiRecognizer(model, sample_rate)
        for offset in range(0, len(audio_bytes), 8000):
            command_recognizer.AcceptWaveform(audio_bytes[offset:offset + 8000])
        full_text = json.loads(command_recognizer.FinalResult()).get("text", "")

command = worker.wake_tail(full_text)
print(json.dumps({"wake_recognized": wake_text, "full_transcript": full_text, "command": command}))
if command != "open chrome":
    raise SystemExit("The offline model did not recover the command after the ARIS wake phrase.")

import importlib.util
import json
import os
import tempfile
import wave
from pathlib import Path

import numpy as np
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
target_rate = 48000
with tempfile.TemporaryDirectory(prefix="aris-wake-check-") as folder:
    audio_path = Path(folder) / "wake.wav"
    engine = pyttsx3.init()
    engine.save_to_file(phrase, str(audio_path))
    engine.runAndWait()
    engine.stop()
    model = Model(str(model_path))
    with wave.open(str(audio_path), "rb") as audio:
        source_rate = audio.getframerate()
        channels = audio.getnchannels()
        pcm = np.frombuffer(audio.readframes(audio.getnframes()), dtype=np.int16)
        if channels > 1:
            pcm = pcm.reshape((-1, channels)).astype(np.float32).mean(axis=1)
        sample_positions = np.arange(round(len(pcm) * target_rate / source_rate), dtype=np.float64) * source_rate / target_rate
        pcm_48k = np.interp(sample_positions, np.arange(len(pcm)), pcm.astype(np.float32)).clip(-32768, 32767).astype(np.int16).tobytes()
        worker.active_sample_rate = target_rate
        wake_recognizer = KaldiRecognizer(model, target_rate, worker.WAKE_GRAMMAR)
        for offset in range(0, len(pcm_48k), 8000):
            wake_recognizer.AcceptWaveform(pcm_48k[offset:offset + 8000])
        wake_text = json.loads(wake_recognizer.FinalResult()).get("text", "")
        if worker.wake_tail(wake_text) is None:
            raise SystemExit("The offline model did not detect the configured Iris wake phrase: " + wake_text)

        command_recognizer = KaldiRecognizer(model, target_rate)
        for offset in range(0, len(pcm_48k), 8000):
            command_recognizer.AcceptWaveform(pcm_48k[offset:offset + 8000])
        full_text = json.loads(command_recognizer.FinalResult()).get("text", "")

command = worker.wake_tail(full_text)
print(json.dumps({"sample_rate": target_rate, "wake_recognized": wake_text, "full_transcript": full_text, "command": command}))
if command != "open chrome":
    raise SystemExit("The offline model did not recover the command at the microphone's supported sample rate.")

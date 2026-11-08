import json
import os
import sys
import tempfile
import wave
from pathlib import Path

import pyttsx3
from vosk import KaldiRecognizer, Model, SetLogLevel

SetLogLevel(-1)
phrase = "Hello there."
model_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    os.environ.get("ARIS_VOSK_MODEL_DIR", "")
)
if not (model_path / "am").is_dir():
    raise SystemExit("Offline speech model not found: " + str(model_path))

with tempfile.TemporaryDirectory(prefix="aris-voice-check-") as folder:
    audio_path = Path(folder) / "speech.wav"
    engine = pyttsx3.init()
    engine.setProperty("rate", 155)
    engine.save_to_file(phrase, str(audio_path))
    engine.runAndWait()
    engine.stop()

    if not audio_path.exists() or audio_path.stat().st_size < 1024:
        raise SystemExit("Offline speech synthesis did not create a WAV file.")

    model = Model(str(model_path))
    with wave.open(str(audio_path), "rb") as audio:
        if audio.getnchannels() != 1 or audio.getsampwidth() != 2:
            raise SystemExit("Smoke test expects mono 16-bit PCM speech audio.")
        recognizer = KaldiRecognizer(model, audio.getframerate())
        while True:
            data = audio.readframes(4000)
            if not data:
                break
            recognizer.AcceptWaveform(data)
        result = json.loads(recognizer.FinalResult())

transcript = result.get("text", "").strip()
print(json.dumps({"synthesized": True, "transcript": transcript}))
if "hello there" not in transcript:
    raise SystemExit("Offline speech recognition did not match the generated phrase: " + transcript)

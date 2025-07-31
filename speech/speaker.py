import pyttsx3
import json
import requests
import os
import tempfile
from playsound import playsound
import time

class Speaker:
    def __init__(self):
        with open("config.json") as f:
            config = json.load(f)
        self.voice_type = config.get("voice", "female")
        self.use_elevenlabs = config.get("use_elevenlabs", False)
        self.elevenlabs_api_key = config.get("elevenlabs_api_key")
        self.elevenlabs_voice = config.get("elevenlabs_voice", "Rachel")

    def speak(self, text):
        print(f"Aris: {text}")

        if self.use_elevenlabs and self.elevenlabs_api_key:
            try:
                self._speak_elevenlabs(text)
                return
            except Exception as e:
                print(f"[!] ElevenLabs failed, falling back to pyttsx3: {e}")

        # Fallback to pyttsx3
        self._speak_pyttsx3(text)

    def _speak_elevenlabs(self, text):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice}"
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            raise Exception(f"ElevenLabs API error: {response.text}")

        # Save and play audio with cleanup
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(response.content)
            tmp_file.flush()
            audio_path = tmp_file.name

        try:
            playsound(audio_path)
            time.sleep(0.1)  # small delay to ensure file is released
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)

    def _speak_pyttsx3(self, text):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        for voice in voices:
            if self.voice_type.lower() == "female" and "female" in voice.name.lower():
                engine.setProperty('voice', voice.id)
            elif self.voice_type.lower() == "male" and "male" in voice.name.lower():
                engine.setProperty('voice', voice.id)

        engine.setProperty('rate', 165)
        engine.say(text)
        engine.runAndWait()
        engine.stop()

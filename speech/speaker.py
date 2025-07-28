import pyttsx3
import json

class Speaker:
    def __init__(self):
        with open("config.json") as f:
            config = json.load(f)
        self.voice_type = config.get("voice", "male")

    def speak(self, text):
        print(f"Aris: {text}")
        engine = pyttsx3.init()  # ⚠️ Re-init engine every time (avoids freeze)
        voices = engine.getProperty('voices')
        
        for voice in voices:
            if self.voice_type.lower() == "female" and "female" in voice.name.lower():
                engine.setProperty('voice', voice.id)
            elif self.voice_type.lower() == "male" and "male" in voice.name.lower():
                engine.setProperty('voice', voice.id)

        engine.setProperty('rate', 165)
        engine.say(text)
        engine.runAndWait()
        engine.stop()  # forcefully release audio resource

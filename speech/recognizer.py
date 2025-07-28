import speech_recognition as sr
import json
from speech.speaker import Speaker

speaker = Speaker()
speak = speaker.speak

# Load the config memory
with open("config.json") as f:
    config = json.load(f)

def listen():
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening...")
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio)
        print(f"You said: {command}")
        return command
    except sr.UnknownValueError:
        print("Sorry, I didn't catch that.")
        return None
    except sr.RequestError:
        print("Network error.")
        return None

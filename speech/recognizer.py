import speech_recognition as sr
import json
from speech.speaker import Speaker

speaker = Speaker()
speak = speaker.speak

# Load the config memory
with open("config.json") as f:
    config = json.load(f)

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=6)
            command = r.recognize_google(audio)
            print(f"You said: {command}")
            
            # Update last command in memory
            config['memory']['last_command'] = command
            with open("config.json", "w") as f:
                json.dump(config, f)
                
            return command
        except sr.WaitTimeoutError:
            print("No speech detected.")
            speak("I didn't hear anything. Could you try again?")
            return ""
        except sr.UnknownValueError:
            print("Could not understand audio.")
            speak("I didn't catch that. Could you please repeat?")
            return ""
        except sr.RequestError:
            print("Speech service is unavailable.")
            speak("Sorry, the speech service is down.")
            return ""

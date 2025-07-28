import speech_recognition as sr
from speech.speaker import Speaker

speaker = Speaker()
speak = speaker.speak

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=6)
            command = r.recognize_google(audio)
            print(f"You said: {command}")
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

import webbrowser
import pyautogui
import time

# Import your local TTS and voice recognition modules
from speech.speaker import Speaker
from speech.recognizer import listen

# Initialize speaker
speaker = Speaker()

def speak(text):
    speaker.speak(text)

def search_youtube(query):
    """Opens YouTube search results in browser."""
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Opened YouTube search results for: {query}"

def open_youtube_search_and_listen(query):
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    webbrowser.open(url)
    speak(f"Opened YouTube search results for: {query}")
    time.sleep(5)  # Wait for page to load

    speak("Which video should I play? Say first, second, or third.")
    selection = listen().lower()

    video_positions = {
        "first": (300, 350),
        "second": (300, 500),
        "third": (300, 650)
    }

    for key in video_positions:
        if key in selection:
            x, y = video_positions[key]
            pyautogui.moveTo(x, y)
            pyautogui.click()
            speak(f"Playing the {key} video.")
            time.sleep(7)  # wait for video to buffer/load
            pyautogui.press('f')  # Fullscreen
            return control_youtube_playback()  # Enter playback control mode

    speak("Sorry, I didn't catch that. Say first, second, or third.")

def control_youtube_playback():
    speak("You can say pause, resume, forward, back, fullscreen, next, previous, or stop.")

    while True:
        command = listen().lower()

        if "pause" in command or "resume" in command:
            pyautogui.press('k')
        elif "forward" in command:
            pyautogui.press('l')
        elif "back" in command:
            pyautogui.press('j')
        elif "full screen" in command or "fullscreen" in command:
            pyautogui.press('f')
        elif "next" in command:
            pyautogui.press('shift+n')  # Next video
        elif "previous" in command:
            pyautogui.press('shift+p')  # Previous video
        elif "stop" in command or "exit" in command:
            speak("Stopping video control.")
            break
        else:
            speak("Command not understood. Try pause, resume, forward, back, fullscreen, next, or stop.")
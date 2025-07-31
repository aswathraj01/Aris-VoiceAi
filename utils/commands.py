import os
import re
import webbrowser
import pyautogui
import platform
import subprocess
from speech.speaker import Speaker
from aris_brain import ask_aris_llm  # LLama-based response generator
import psutil

speaker = Speaker()
speak = speaker.speak


def extract_app_name(command):
    # Clean command
    command = command.lower()
    for word in ["can you", "could you", "please", "the", "app", "application", "open", "launch", "start", "?"]:
        command = command.replace(word, "")
    return command.strip()


def open_app(command):
    app_name = extract_app_name(command)

    if not app_name:
        response = ask_aris_llm("The user asked to open an app but didn't mention which one. Give a helpful response.")
        speak(response)
        return response

    try:
        opened = False

        if app_name in ["calculator", "calc"]:
            subprocess.Popen("calc.exe")
            opened = True
        elif app_name in ["notepad"]:
            subprocess.Popen("notepad.exe")
            opened = True
        elif app_name in ["google chrome", "chrome"]:
            subprocess.Popen(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
            opened = True
        # Add more apps here...

        if opened:
            response = ask_aris_llm(f"tell the user that you have opened {app_name} successfully, and what should you do next? nothing more.")
        else:
            response = ask_aris_llm(f"You couldn't find a way to open {app_name}. Give a polite response explaining that you couldn't find the app, and ask if they want to try something else.")

        return response


    except Exception as e:
        response = ask_aris_llm(f"I tried to open {app_name} but failed with this error: {str(e)}. Respond accordingly.")
        speak(response)
        return response

def close_app(command):
    app_name = extract_app_name(command)

    if not app_name:
        response = ask_aris_llm("The user asked to close an app but didn't specify which one. Respond politely and ask for clarification.")
        speak(response)
        return 

    try:
        closed = False

        if app_name in ["calculator", "calc"]:
            os.system("taskkill /f /im calc.exe")
            closed = True
        elif app_name in ["notepad"]:
            os.system("taskkill /f /im notepad.exe")
            closed = True
        elif app_name in ["chrome", "google chrome"]:
            os.system("taskkill /f /im chrome.exe")
            closed = True

        if closed:
            response = ask_aris_llm(f"Calculator (or {app_name}) closed successfully. Respond as a friendly assistant.")
        else:
            response = ask_aris_llm(f"I couldn't find the app '{app_name}' running, so I couldn't close it. Ask the user if they want to try something else.")

        speak(response)
        return response

    except Exception as e:
        response = ask_aris_llm(f"I tried to close {app_name} but got this error: {str(e)}. Respond accordingly.")
        speak(response)
        return response


def take_screenshot():
    index = 1
    while os.path.exists(f"screenshot_{index}.png"):
        index += 1

    filename = f"screenshot/screenshot_{index}.png"
    pyautogui.screenshot().save(filename)

    if index == 1:
        response = ask_aris_llm(f"A screenshot was taken and saved as {filename}. Respond to the user accordingly.")
        speak(response)

    else:
        response = ask_aris_llm(f"Another screenshot was taken and saved as {filename}. Respond to the user accordingly. and ask if they need anything else.")
        speak(response)

    return


def lock_system():
    speak("Locking the system now.")
    if platform.system() == "Windows":
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif platform.system() == "Linux":
        os.system("gnome-screensaver-command -l")
    return "System locked."


def shutdown():
    speak("Shutting down the system now.")
    if platform.system() == "Windows":
        os.system("shutdown /s /t 1")
    elif platform.system() == "Linux":
        os.system("shutdown now")
    return "System is shutting down."


def restart():
    speak("Restarting your system now.")
    if platform.system() == "Windows":
        os.system("shutdown /r /t 1")
    elif platform.system() == "Linux":
        os.system("reboot")
    return "System is restarting."


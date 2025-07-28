import os
import webbrowser
import pyautogui
import platform
import subprocess

def open_app(app_name):
    app_name = app_name.lower()

    if "chrome" in app_name:
        os.system("start chrome")
    elif "notepad" in app_name:
        os.system("start notepad")
    elif "vs code" in app_name or "code" in app_name:
        os.system("code")
    elif "calculator" in app_name:
        os.system("start calc")
    else:
        return f"I don’t know how to open {app_name} yet."

    return f"Opening {app_name}."

def take_screenshot():
    filename = "screenshot.png"
    pyautogui.screenshot().save(filename)
    return f"Screenshot saved as {filename}."

def lock_system():
    if platform.system() == "Windows":
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif platform.system() == "Linux":
        os.system("gnome-screensaver-command -l")
    return "Locking the system."

def shutdown():
    if platform.system() == "Windows":
        os.system("shutdown /s /t 1")
    elif platform.system() == "Linux":
        os.system("shutdown now")
    return "Shutting down now."

def restart():
    if platform.system() == "Windows":
        os.system("shutdown /r /t 1")
    elif platform.system() == "Linux":
        os.system("reboot")
    return "Restarting the system."

from speech.recognizer import listen
from speech.speaker import Speaker
import json
from utils import commands


speaker = Speaker()
speak = speaker.speak


# Load config
with open("config.json") as f:
    config = json.load(f)

user_name = config["user_name"]
assistant_name = config["assistant_name"]

def handle_command(command):
    if "hello" in command:
        if config["personality"] == "friendly":
            speak(f"Hey {config['user_nickname']}! Nice to hear you.")
        elif config["personality"] == "serious":
            speak(f"Hello. Awaiting your instructions.")
        else:
            speak(f"Hi {config['user_name']}.")
    
    elif "how are you" in command:
        speak("I'm just a bunch of code, but I'm feeling awesome. Thanks for asking!")

    elif "what's my name" in command:
        speak(f"You are {config['user_name']}, aka {config['user_nickname']}. My favorite human.")

    elif "favorite music" in command:
        speak(f"You love {config['user_favorites']['music']} music.")
    
    elif "open" in command:
        result = commands.open_app(command)
        speak(result)

    elif "screenshot" in command:
        result = commands.take_screenshot()
        speak(result)

    elif "lock" in command:
        speak(commands.lock_system())

    elif "shutdown" in command:
        speak(commands.shutdown())

    elif "restart" in command:
        speak(commands.restart())

    elif "exit" in command:
        speak("Shutting down. Take care.")
        exit()

    else:
        speak("I'm still learning that command, bro.")

# Main loop
if __name__ == "__main__":
    speak(f"Hello {user_name}, this is {assistant_name} speaking.")
    while True:
        command = listen()
        if command:
            handle_command(command.lower())

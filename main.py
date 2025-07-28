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
        speak(f"Hey {config['user_nickname']}! Nice to hear you.")
    elif "how are you" in command:
        speak("I'm doing great! Hope you are too.")
    elif "what's my name" in command:
        speak(f"You are {config['user_name']}, aka {config['user_nickname']}.")
    elif "birthday" in command:
        speak(f"Your birthday is on {config['memory']['birthday']}.")
    elif "favorite food" in command:
        speak(f"Your favorite food is {config['memory']['favorite_food']}.")
    elif "last command" in command:
        last_command = config['memory'].get('last_command', 'I don’t remember.')
        speak(f"Your last command was: {last_command}")
    elif "favorite music" in command:
        speak(f"Your favorite music is {config['user_favorites']['music']}.")
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
        speak("Goodbye.")
        exit()
    else:
        speak(f"I’m still learning that command, bro. You said: {command}")



# Main loop
if __name__ == "__main__":
    speak(f"Hello {user_name}, this is {assistant_name} speaking.")
    while True:
        command = listen()
        if command:
            handle_command(command.lower())

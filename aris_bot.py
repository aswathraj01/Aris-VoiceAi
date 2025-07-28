from speech.recognizer import listen
from speech.speaker import Speaker
import json
from utils import commands
from ollama import Client
import time
from utils.commands import close_app


client = Client(host='http://localhost:11434')
speaker = Speaker()
speak = speaker.speak

# Load config
with open("config.json") as f:
    config = json.load(f)

user_name = config["user_name"]
assistant_name = config["assistant_name"]

# LLaMA fallback response
def generate_response(prompt):
    full_prompt = f"The following is a conversation with {assistant_name}, a helpful AI assistant.\n\nHuman: {prompt}\n{assistant_name}:"
    response = client.chat(
        model='llama3',
        messages=[{"role": "user", "content": full_prompt}]
    )
    return response['message']['content']

# Command handler
def handle_command(command):
    command = command.lower()

    if "exit" in command or "quit" in command or "stop" in command:
        speak("Goodbye.")
        return "exit"

    elif "hello" in command:
        speak(f"Hey {config['user_nickname']}! Nice to hear you.")
        return True

    elif "how are you" in command:
        speak("I'm doing great! Hope you are too.")
        return True

    elif "what's my name" in command:
        speak(f"You are {config['user_name']}, aka {config['user_nickname']}.")
        return True

    elif "birthday" in command:
        speak(f"Your birthday is on {config['memory']['birthday']}.")
        return True

    elif "favorite food" in command:
        speak(f"Your favorite food is {config['memory']['favorite_food']}.")
        return True

    elif "last command" in command:
        last_command = config['memory'].get('last_command', 'I don’t remember.')
        speak(f"Your last command was: {last_command}")
        return True

    elif "favorite music" in command:
        speak(f"Your favorite music is {config['user_favorites']['music']}.")
        return True

    elif "open" in command:
        result = commands.open_app(command)
        speak(result)
        return True

    elif "close" in command:
        response = close_app(command)
        print("Aris:", response)

    elif "screenshot" in command:
        result = commands.take_screenshot()
        speak(result)
        return True

    elif "lock" in command:
        speak(commands.lock_system())
        return True

    elif "shutdown" in command:
        speak(commands.shutdown())
        return True

    elif "restart" in command:
        speak(commands.restart())
        return True

    return False  # Not a recognized command


# Main loop
if __name__ == "__main__":
    speak(f"Hello, this is {assistant_name} speaking.")
    time.sleep(0.5)

    while True:
        command = listen()
        if command:
            result = handle_command(command)
            if result == "exit":
                break
            elif result is False:
                reply = generate_response(command)
                speak(reply)

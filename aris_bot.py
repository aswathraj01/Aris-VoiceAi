from speech.recognizer import listen
from speech.speaker import Speaker
import json
from utils import commands
from ollama import Client
import re
import os
import time
from utils.commands import close_app
from utils.code_editor import write_to_file, replace_line, open_in_vscode, append_to_file
from aris_brain import ask_aris_llm # LLama-based response generator
from utils.web_search import search_youtube
from utils.memory_manager import append_to_conversation



client = Client(host='http://localhost:11434')
speaker = Speaker()
speak = speaker.speak

# Load config
with open("config.json") as f:
    config = json.load(f)

user_name = config["user_name"]
assistant_name = config["assistant_name"]


def extract_code_blocks(text):
    code_blocks = re.findall(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    return [block.strip() for block in code_blocks]

def ask_aris(prompt):
    print(f"Prompt to Aris: {prompt}")
    full_prompt = f"Write Python code for this: {prompt}"
    response = ask_aris_llm(full_prompt)  # calling aris_brain's ask_aris renamed to avoid conflict
    print("Aris raw response:", response)
    speak("Let me think...")

    # Extract code only
    code_blocks = extract_code_blocks(response)

    if not code_blocks:
        speak("Hmm, I didn't find any valid code in that response.")
        return None

    elif len(code_blocks) == 1:
        return code_blocks[0]

    else:
        # Multiple code blocks found — ask the user
        speak("I found multiple versions. Do you want the first or second one?")
        user_choice = listen().lower()
        if "first" in user_choice:
            return code_blocks[0]
        elif "second" in user_choice:
            return code_blocks[1]
        else:
            speak("I didn't get that. Using the first version.")
            return code_blocks[0]
        

last_intent = None  # global or maintained in a class


# Command handler
def handle_command(command):
    
    global last_intent

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
    
    
    #intelligent mode
    elif any(phrase in command for phrase in [
        "turn on intelligent mode",
        "activate intelligent mode",
        "start intelligent mode",
        "switch to intelligent mode",
        "turn on intelligent",
        "activate intelligent",
        "start intelligent",
        "switch to intelligent",
    ]):
        response = commands.intelligent_mode()
        speak(response)
        return True


    elif "deactivate intelligent mode" in command or "normal mode" in command:
        response = commands.deactivate_intelligent_mode()
        speak(response)
        return True


    #code-related commands
    elif "write a code" in command or "add a function" in command:
        speak("Okay, tell me what to code.")
        code_prompt = listen()
        aris_response = ask_aris(code_prompt)

        if "def" in aris_response or "print" in aris_response or "import" in aris_response:
            filename = "generated_code.py"
            result = append_to_file(filename, aris_response)
            speak(result)
            open_in_vscode(filename)
        else:
            speak("Got it. But I didn't detect any code to save.")
        return True
    
    elif "search" in command.lower():
        command_lower = command.lower()

        if "youtube" in command_lower:
            # Extract the search query from commands like:
            # "search for relaxing music on youtube"
            query = command_lower

            # Remove common phrases
            for phrase in ["search for", "search", "on youtube", "youtube"]:
                query = query.replace(phrase, "")

            query = query.strip()

            if not query:
                speaker.speak("What do you want me to search for on YouTube?")
                query = Listener.listen().strip()

            # Use the improved YouTube search and control function
            search_result = search_youtube(query)  # It will handle everything
            # No need to speak anything else — that function does all interactions

        else:
            speaker.speak("Sorry, I can only search YouTube for now.")


    # System commands
    elif "lock" in command:
        speak(commands.lock_system())
        return True

    elif "shutdown" in command:
        speak(commands.shutdown())
        return True

    elif "restart" in command:
        speak(commands.restart())
        return True

    return False  

# Main loop
if __name__ == "__main__":
    speak(f"OK, {assistant_name} is active now.")
    time.sleep(0.5)

    while True:
        command = listen()
        if command:
            result = handle_command(command)
            if result == "exit":
                break
            elif result is False:
                reply = ask_aris_llm(command)
                speak(reply)
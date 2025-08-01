import json
import os

# Paths
DATA_PATH = "data"
CONVO_FILE = os.path.join(DATA_PATH, "conversation.json")

# Ensure data directory exists
os.makedirs(DATA_PATH, exist_ok=True)

# Create file if it doesn't exist or is invalid
if not os.path.exists(CONVO_FILE):
    with open(CONVO_FILE, "w") as f:
        json.dump([], f)

def load_conversations():
    try:
        with open(CONVO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_conversations(conversations):
    with open(CONVO_FILE, "w") as f:
        json.dump(conversations, f, indent=2)

def append_to_conversation(user_input, aris_reply):
    conversations = load_conversations()
    conversations.append({
        "user": user_input.strip(),
        "aris": aris_reply.strip()
    })
    save_conversations(conversations)

def add_conversation(prompt, response):
    append_to_conversation(prompt, response)

import requests
from utils.web_fallback import search_and_get_answer
from utils.memory_manager import append_to_conversation, add_conversation, load_conversations  # ✅ fixed import

def get_contextual_prompt(user_prompt):
    memory = load_conversations()  # ✅ fixed typo: was 'load_conversation'
    history = "\n".join([f"User: {item['user']}\nAris: {item['aris']}" for item in memory[-5:]])
    return f"{history}\nUser: {user_prompt}\nAris:"

def ask_aris_llm(prompt):
    full_prompt = get_contextual_prompt(prompt)

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": full_prompt,
                "stream": False
            }
        )

        if response.status_code == 200:
            data = response.json()
            llm_reply = data.get("response", "").strip()

            # Fallback if the model is not confident
            if not llm_reply or any(x in llm_reply.lower() for x in ["i don't know", "not sure", "unsure"]):
                fallback = search_and_get_answer(prompt)
                append_to_conversation(prompt, fallback)
                return fallback

            append_to_conversation(prompt, llm_reply)
            return llm_reply

        else:
            return f"Error: {response.status_code} - {response.text}"

    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the LLaMA 3 server. Is Ollama running?"

    except Exception as e:
        return f"Unexpected error: {str(e)}"

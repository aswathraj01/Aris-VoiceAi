import requests
from web_fallback import search_and_get_answer  # Import the web search fallback

def ask_aris_llm(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
        )

        if response.status_code == 200:
            data = response.json()
            llm_reply = data.get("response", "")
            if not llm_reply or "I don't know" in llm_reply.lower() or "unsure" in llm_reply.lower():
                return search_and_get_answer(prompt)  # Fallback to web
            return llm_reply
        else:
            return f"Error: {response.status_code} - {response.text}"

    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the LLaMA 3 server. Is Ollama running?"

    except Exception as e:
        return f"Unexpected error: {str(e)}"

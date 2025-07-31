import requests

def ask_aris_llm(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",  # Make sure this matches your Ollama model name
                "prompt": prompt,
                "stream": False
            }
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("response", "Sorry, I didn't get a response.")
        else:
            return f"Error: {response.status_code} - {response.text}"

    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the LLaMA 3 server. Is Ollama running?"

    except Exception as e:
        return f"Unexpected error: {str(e)}"

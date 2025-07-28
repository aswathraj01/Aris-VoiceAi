import requests

def ask_aris(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",  # or whatever name you used when running `ollama run llama3`
            "prompt": prompt,
            "stream": False
        }
    )

    if response.status_code == 200:
        data = response.json()
        return data.get("response", "Sorry, I didn't get a response.")
    else:
        return f"Error: {response.status_code} - {response.text}"

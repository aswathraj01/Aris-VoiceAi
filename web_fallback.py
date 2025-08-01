import requests

def search_and_get_answer(query):
    try:
        response = requests.get(f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1")
        data = response.json()
        if data.get("Abstract"):
            return data["Abstract"]
        elif data.get("RelatedTopics"):
            for topic in data["RelatedTopics"]:
                if isinstance(topic, dict) and topic.get("Text"):
                    return topic["Text"]
        return "I searched the web but couldn't find a clear answer."
    except Exception as e:
        return f"Web search failed: {str(e)}"

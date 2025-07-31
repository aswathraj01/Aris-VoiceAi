import webbrowser

def search_youtube(query):
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Opened YouTube search results for: {query}"

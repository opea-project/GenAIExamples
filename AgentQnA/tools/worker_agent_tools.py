import requests
import os

def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for a specific query."""
    url = os.environ.get("RETRIEVAL_TOOL_URL")
    print(url)
    proxies = {"http": ""}
    payload = {
        "text": query,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    print(response)
    docs = response.json()["documents"]
    context = ""
    for i, doc in enumerate(docs):
        if i == 0:
            context = doc
        else:
            context += "\n" + doc
    print(context)
    return context
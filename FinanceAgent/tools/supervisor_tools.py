import requests
import os

def finqa_agent(query:str):
    url = os.environ.get("WORKER_FINQA_AGENT_URL")
    print(url)
    proxies = {"http": ""}
    payload = {
        "messages": query,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    return response.json()["text"]

def summarize_doc(doc_title):
    pass

def research_agent(company:str):
    url = os.environ.get("WORKER_RESEARCH_AGENT_URL")
    print(url)
    proxies = {"http": ""}
    payload = {
        "messages": company,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    return response.json()["text"]
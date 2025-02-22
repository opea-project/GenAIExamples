# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import requests


def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for a specific query."""
    url = os.environ.get("RETRIEVAL_TOOL_URL")
    print(url)
    proxies = {"http": ""}
    payload = {"messages": query, "k": 5, "top_n": 2}
    response = requests.post(url, json=payload, proxies=proxies)
    print(response)
    if "documents" in response.json():
        docs = response.json()["documents"]
        context = ""
        for i, doc in enumerate(docs):
            context += f"Doc[{i+1}]:\n{doc}\n"
        return context
    elif "text" in response.json():
        return response.json()["text"]
    elif "reranked_docs" in response.json():
        docs = response.json()["reranked_docs"]
        context = ""
        for i, doc in enumerate(docs):
            context += f"Doc[{i+1}]:\n{doc}\n"
        return context
    else:
        return "Error parsing response from the knowledge base."


if __name__ == "__main__":
    resp = search_knowledge_base("What is OPEA?")
    # resp = search_knowledge_base("Thriller")
    print(resp)

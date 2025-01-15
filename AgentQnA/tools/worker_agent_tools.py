# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import requests


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
    if "documents" in response.json():
        docs = response.json()["documents"]
        context = ""
        for i, doc in enumerate(docs):
            if i == 0:
                context = doc
            else:
                context += "\n" + doc
        # print(context)
        return context
    elif "text" in response.json():
        return response.json()["text"]
    elif "reranked_docs" in response.json():
        docs = response.json()["reranked_docs"]
        context = ""
        for i, doc in enumerate(docs):
            if i == 0:
                context = doc["text"]
            else:
                context += "\n" + doc["text"]
        # print(context)
        return context
    else:
        return "Error parsing response from the knowledge base."

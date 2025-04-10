# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Any

import requests


def search_knowledge_base(query: str, args: Any) -> str:
    """Search the knowledge base for a specific query."""
    url = os.environ.get("RETRIEVAL_TOOL_URL", "http://localhost:8889/v1/retrievaltool")
    print(url)
    proxies = {"http": ""}
    payload = {"messages": query, "k": args.k, "top_n": args.top_n}
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
    import argparse

    parser = argparse.ArgumentParser(description="Test the knowledge base search.")
    parser.add_argument("--k", type=int, default=5, help="retriever top k")
    parser.add_argument("--top_n", type=int, default=2, help="reranker top n")
    args = parser.parse_args()

    resp = search_knowledge_base("What is OPEA?", args)

    print(resp)

    if not resp.startswith("Error"):
        print("Test successful!")

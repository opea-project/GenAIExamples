# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse

import requests


def search_knowledge_base(query: str, url: str) -> str:
    """Search the knowledge base for a specific query."""
    print(url)
    proxies = {"http": ""}
    payload = {
        "messages": "",
        "input": query,
        "k": 5,
        "top_n": 2,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    print(response)
    if "documents" in response.json():
        docs = response.json()["documents"]
        context = ""
        for i, doc in enumerate(docs):
            if i == 0:
                context = str(i) + ": " + doc
            else:
                context += "\n" + str(i) + ": " + doc
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


def main():
    parser = argparse.ArgumentParser(description="Index data")
    parser.add_argument("--host_ip", type=str, default="localhost", help="Host IP")
    parser.add_argument("--port", type=int, default=8889, help="Port")
    args = parser.parse_args()
    print(args)

    host_ip = args.host_ip
    port = args.port
    url = "http://{host_ip}:{port}/v1/retrievaltool".format(host_ip=host_ip, port=port)

    response = search_knowledge_base("OPEA", url)

    print(response)


if __name__ == "__main__":
    main()

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import requests


def finqa_agent(query: str):
    url = os.environ.get("WORKER_FINQA_AGENT_URL")
    print(url)
    proxies = {"http": ""}
    payload = {
        "messages": query,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    return response.json()["text"]


def research_agent(company: str):
    url = os.environ.get("WORKER_RESEARCH_AGENT_URL")
    print(url)
    proxies = {"http": ""}
    payload = {
        "messages": company,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    return response.json()["text"]

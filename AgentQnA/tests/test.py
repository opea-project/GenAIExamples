# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import requests


def generate_answer_agent_api(url, prompt):
    proxies = {"http": ""}
    payload = {
        "query": prompt,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    answer = response.json()["text"]
    return answer


if __name__ == "__main__":
    ip_address = os.getenv("ip_address", "localhost")
    agent_port = os.getenv("agent_port", "9095")
    url = f"http://{ip_address}:{agent_port}/v1/chat/completions"
    prompt = "Tell me about Michael Jackson song thriller"
    answer = generate_answer_agent_api(url, prompt)
    print(answer)

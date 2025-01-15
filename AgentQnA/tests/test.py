# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os

import requests


def generate_answer_agent_api(url, prompt):
    proxies = {"http": ""}
    payload = {
        "messages": prompt,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    answer = response.json()["text"]
    return answer


def process_request(url, query, is_stream=False):
    proxies = {"http": ""}

    payload = {
        "messages": query,
    }

    try:
        resp = requests.post(url=url, json=payload, proxies=proxies, stream=is_stream)
        if not is_stream:
            ret = resp.json()["text"]
            print(ret)
        else:
            for line in resp.iter_lines(decode_unicode=True):
                print(line)
            ret = None

        resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
        return ret
    except requests.exceptions.RequestException as e:
        ret = f"An error occurred:{e}"
        print(ret)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str)
    parser.add_argument("--stream", action="store_true")
    args = parser.parse_args()

    ip_address = os.getenv("ip_address", "localhost")
    agent_port = os.getenv("agent_port", "9090")
    url = f"http://{ip_address}:{agent_port}/v1/chat/completions"
    prompt = args.prompt

    process_request(url, prompt, args.stream)

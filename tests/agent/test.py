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
    parser.add_argument("--stream", action="store_true", help="Stream the response")
    parser.add_argument("--test-sql-agent", action="store_true", help="Test the SQL agent")
    args = parser.parse_args()

    ip_address = os.getenv("ip_address", "localhost")
    url = f"http://{ip_address}:9095/v1/chat/completions"
    if args.test_sql_agent:
        prompt = "How many schools have the average score in Math over 560 in the SAT test?"
    else:
        prompt = "What is OPEA?"

    if args.stream:
        process_request(url, prompt, is_stream=True)
    else:
        answer = generate_answer_agent_api(url, prompt)
        print(answer)

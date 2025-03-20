# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import uuid

import requests


def process_request(url, query, is_stream=False):
    proxies = {"http": ""}
    content = json.dumps(query) if query is not None else None
    try:
        resp = requests.post(url=url, data=content, proxies=proxies, stream=is_stream)
        if not is_stream:
            ret = resp.json()["text"]
        else:
            for line in resp.iter_lines(decode_unicode=True):
                print(line)
            ret = None

        resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
        return ret
    except requests.exceptions.RequestException as e:
        ret = f"An error occurred:{e}"
        return None


def test_worker_agent(args):
    url = f"http://{args.ip_addr}:{args.ext_port}/v1/chat/completions"
    query = {"role": "user", "messages": args.prompt, "stream": "false"}
    ret = process_request(url, query)
    print("Response: ", ret)


def add_message_and_run(url, user_message, thread_id, stream=False):
    print("User message: ", user_message)
    query = {"role": "user", "messages": user_message, "thread_id": thread_id, "stream": stream}
    ret = process_request(url, query, is_stream=stream)
    print("Response: ", ret)


def test_chat_completion_multi_turn(args):
    url = f"http://{args.ip_addr}:{args.ext_port}/v1/chat/completions"
    thread_id = f"{uuid.uuid4()}"

    # first turn
    print("===============First turn==================")
    user_message = "Which artist has the most albums in the database?"
    add_message_and_run(url, user_message, thread_id, stream=args.stream)
    print("===============End of first turn==================")

    # second turn
    print("===============Second turn==================")
    user_message = "Give me a few examples of the artist's albums?"
    add_message_and_run(url, user_message, thread_id, stream=args.stream)
    print("===============End of second turn==================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip_addr", type=str, default="127.0.0.1", help="endpoint ip address")
    parser.add_argument("--ext_port", type=str, default="9090", help="endpoint port")
    parser.add_argument("--stream", action="store_true", help="streaming mode")
    parser.add_argument("--prompt", type=str, help="prompt message")
    parser.add_argument("--agent_role", type=str, default="supervisor", help="supervisor or worker")
    args, _ = parser.parse_known_args()

    print(args)

    if args.agent_role == "supervisor":
        test_chat_completion_multi_turn(args)
    elif args.agent_role == "worker":
        test_worker_agent(args)
    else:
        raise ValueError("Invalid agent role")

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json

import requests
from src.utils import get_args


def test_assistants_http(args):
    proxies = {"http": ""}
    url = f"http://{args.ip_addr}:{args.ext_port}/v1"

    def process_request(api, query, is_stream=False):
        content = json.dumps(query) if query is not None else None
        print(f"send request to {url}/{api}, data is {content}")
        try:
            resp = requests.post(url=f"{url}/{api}", data=content, proxies=proxies, stream=is_stream)
            if not is_stream:
                ret = resp.json()
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

    # step 1. create assistants
    query = {}
    if ret := process_request("assistants", query):
        assistant_id = ret.get("id")
        print("Created Assistant Id: ", assistant_id)
    else:
        print("Error when creating assistants !!!!")
        return

    # step 2. create threads
    query = {}
    if ret := process_request("threads", query):
        thread_id = ret.get("id")
        print("Created Thread Id: ", thread_id)
    else:
        print("Error when creating threads !!!!")
        return

    # step 3. add messages
    if args.query is None:
        query = {"role": "user", "content": "How old was Bill Gates when he built Microsoft?"}
    else:
        query = {"role": "user", "content": args.query}
    if ret := process_request(f"threads/{thread_id}/messages", query):
        pass
    else:
        print("Error when add messages !!!!")
        return

    # step 4. run
    print("You may cancel the running process with cmdline")
    print(f"curl {url}/threads/{thread_id}/runs/cancel -X POST -H 'Content-Type: application/json'")

    query = {"assistant_id": assistant_id}
    process_request(f"threads/{thread_id}/runs", query, is_stream=True)


if __name__ == "__main__":
    args1, _ = get_args()
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", type=str, default="react")
    parser.add_argument("--local_test", action="store_true", help="Test with local mode")
    parser.add_argument("--endpoint_test", action="store_true", help="Test with endpoint mode")
    parser.add_argument("--assistants_api_test", action="store_true", help="Test with endpoint mode")
    parser.add_argument("--q", type=int, default=0)
    parser.add_argument("--ip_addr", type=str, default="127.0.0.1", help="endpoint ip address")
    parser.add_argument("--ext_port", type=str, default="9090", help="endpoint port")
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--filedir", type=str, default="./", help="test file directory")
    parser.add_argument("--filename", type=str, default="query.csv", help="query_list_file")
    parser.add_argument("--output", type=str, default="output.csv", help="query_list_file")
    parser.add_argument("--ut", action="store_true", help="ut")

    args, _ = parser.parse_known_args()

    for key, value in vars(args1).items():
        setattr(args, key, value)

    if args.assistants_api_test:
        print("test args:", args)
        test_assistants_http(args)
    else:
        print("Please specify the test type")

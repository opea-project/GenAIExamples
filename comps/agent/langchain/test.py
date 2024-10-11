# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
import traceback

import pandas as pd
import requests
from src.utils import get_args


def test_agent_local(args):
    from src.agent import instantiate_agent

    if args.q == 0:
        df = pd.DataFrame({"query": ["What is the Intel OPEA Project?"]})
    elif args.q == 1:
        df = pd.DataFrame({"query": ["what is the trade volume for Microsoft today?"]})
    elif args.q == 2:
        df = pd.DataFrame({"query": ["what is the hometown of Year 2023 Australia open winner?"]})

    agent = instantiate_agent(args, strategy=args.strategy)
    app = agent.app

    config = {"recursion_limit": args.recursion_limit}

    traces = []
    success = 0
    for _, row in df.iterrows():
        print("Query: ", row["query"])
        initial_state = {"messages": [{"role": "user", "content": row["query"]}]}
        try:
            trace = {"query": row["query"], "trace": []}
            for event in app.stream(initial_state, config=config):
                trace["trace"].append(event)
                for k, v in event.items():
                    print("{}: {}".format(k, v))

            traces.append(trace)
            success += 1
        except Exception as e:
            print(str(e), str(traceback.format_exc()))
            traces.append({"query": row["query"], "trace": str(e)})

        print("-" * 50)

    df["trace"] = traces
    df.to_csv(os.path.join(args.filedir, args.output), index=False)
    print(f"succeed: {success}/{len(df)}")


def test_agent_http(args):
    proxies = {"http": ""}
    ip_addr = args.ip_addr
    url = f"http://{ip_addr}:9090/v1/chat/completions"

    def process_request(query):
        content = json.dumps({"query": query})
        print(content)
        try:
            resp = requests.post(url=url, data=content, proxies=proxies)
            ret = resp.text
            resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
        except requests.exceptions.RequestException as e:
            ret = f"An error occurred:{e}"
        print(ret)
        return ret

    if args.quick_test:
        df = pd.DataFrame({"query": ["What is the weather today in Austin?"]})
    elif args.quick_test_multi_args:
        df = pd.DataFrame({"query": ["what is the trade volume for Microsoft today?"]})
    else:
        df = pd.read_csv(os.path.join(args.filedir, args.filename))
        df = df.sample(n=2, random_state=42)
    traces = []
    for _, row in df.iterrows():
        ret = process_request(row["query"])
        trace = {"query": row["query"], "trace": ret}
        traces.append(trace)

    df["trace"] = traces
    df.to_csv(os.path.join(args.filedir, args.output), index=False)


def test_assistants_http(args):
    proxies = {"http": ""}
    ip_addr = args.ip_addr
    url = f"http://{ip_addr}:9090/v1"

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


def test_ut(args):
    from src.tools import get_tools_descriptions

    tools = get_tools_descriptions("tools/custom_tools.py")
    for tool in tools:
        print(tool)


if __name__ == "__main__":
    args1, _ = get_args()
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", type=str, default="react")
    parser.add_argument("--local_test", action="store_true", help="Test with local mode")
    parser.add_argument("--endpoint_test", action="store_true", help="Test with endpoint mode")
    parser.add_argument("--assistants_api_test", action="store_true", help="Test with endpoint mode")
    parser.add_argument("--q", type=int, default=0)
    parser.add_argument("--ip_addr", type=str, default="127.0.0.1", help="endpoint ip address")
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--filedir", type=str, default="./", help="test file directory")
    parser.add_argument("--filename", type=str, default="query.csv", help="query_list_file")
    parser.add_argument("--output", type=str, default="output.csv", help="query_list_file")
    parser.add_argument("--ut", action="store_true", help="ut")

    args, _ = parser.parse_known_args()

    for key, value in vars(args1).items():
        setattr(args, key, value)

    if args.local_test:
        test_agent_local(args)
    elif args.endpoint_test:
        test_agent_http(args)
    elif args.ut:
        test_ut(args)
    elif args.assistants_api_test:
        test_assistants_http(args)
    else:
        print("Please specify the test type")

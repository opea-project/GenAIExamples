# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
import timeit

import pandas as pd
import requests


def test_text(ip_addr="localhost", batch_size=1):
    proxies = {"http": ""}
    url = "http://localhost:8060/v1/graphs"

    # payload = {"text":"MATCH (t:Task {status:'open'}) RETURN count(*)","strtype":"cypher"}
    content = {"text": "MATCH (t:Task {status:'open'}) RETURN count(*)"}
    payload = {"input": json.dumps(content)}

    try:
        resp = requests.post(url=url, data=payload, proxies=proxies)
        print(resp.text)
        resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
        print("Request successful!")
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch_size", type=int, default=1, help="Batch size for testing")
    parser.add_argument("--ip_addr", type=str, default="localhost", help="IP address of the server")

    args = parser.parse_args()
    test_text(ip_addr=args.ip_addr, batch_size=args.batch_size)

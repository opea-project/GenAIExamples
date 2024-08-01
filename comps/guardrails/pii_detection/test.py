# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os

import requests
from utils import Timer


def test_html(ip_addr="localhost", batch_size=20, strategy=None):
    import pandas as pd

    proxies = {"http": ""}
    url = f"http://{ip_addr}:6357/v1/piidetect"
    urls = ["https://opea.dev/"] * batch_size
    payload = {"link_list": json.dumps(urls), "strategy": strategy}

    with Timer(f"send {len(urls)} link to pii detection endpoint"):
        try:
            resp = requests.post(url=url, data=payload, proxies=proxies)
            print(resp.text)
            resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
            print("Request successful!")
        except requests.exceptions.RequestException as e:
            print("An error occurred:", e)


def test_text(ip_addr="localhost", batch_size=20, strategy=None):
    proxies = {"http": ""}
    url = f"http://{ip_addr}:6357/v1/piidetect"

    content = [
        "Q1 revenue was $1.23 billion, up 12% year over year. ",
        "We are excited to announce the opening of our new office in Miami! ",
        "Mary Smith, 123-456-7890,",
        "John is a good team leader",
        "meeting minutes: sync up with sales team on the new product launch",
    ]

    payload = {"text_list": json.dumps(content), "strategy": strategy}

    with Timer(f"send {len(content)} text to pii detection endpoint"):
        try:
            resp = requests.post(url=url, data=payload, proxies=proxies)
            print(resp.text)
            resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
            print("Request successful!")
        except requests.exceptions.RequestException as e:
            print("An error occurred:", e)


def test_pdf(ip_addr="localhost", batch_size=20):
    proxies = {"http": ""}
    url = f"http://{ip_addr}:6357/v1/piidetect"
    dir_path = "data/pdf"
    file_list = os.listdir(dir_path)
    file_list = file_list[:batch_size]
    files = [("files", (f, open(os.path.join(dir_path, f), "rb"), "application/pdf")) for f in file_list]
    with Timer(f"send {len(files)} documents to pii detection endpoint"):
        try:
            resp = requests.request("POST", url=url, headers={}, files=files, proxies=proxies)
            print(resp.text)
            resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
            print("Request successful!")
        except requests.exceptions.RequestException as e:
            print("An error occurred:", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_html", action="store_true", help="Test HTML pii detection")
    parser.add_argument("--test_pdf", action="store_true", help="Test PDF pii detection")
    parser.add_argument("--test_text", action="store_true", help="Test Text pii detection")
    parser.add_argument("--batch_size", type=int, default=20, help="Batch size for testing")
    parser.add_argument("--ip_addr", type=str, default="localhost", help="IP address of the server")
    parser.add_argument("--strategy", type=str, default="ml", help="Strategy for pii detection")

    args = parser.parse_args()

    print(args)

    if args.test_html:
        test_html(ip_addr=args.ip_addr, batch_size=args.batch_size)
    elif args.test_pdf:
        test_pdf(ip_addr=args.ip_addr, batch_size=args.batch_size)
    elif args.test_text:
        test_text(ip_addr=args.ip_addr, batch_size=args.batch_size, strategy=args.strategy)
    else:
        print("Please specify the test type")

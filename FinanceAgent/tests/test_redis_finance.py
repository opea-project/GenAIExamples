# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os

import requests


def test_html(url, link_list):
    proxies = {"http": ""}
    payload = {"link_list": json.dumps(link_list)}
    try:
        resp = requests.post(url=url, data=payload, proxies=proxies)
        print(resp.text)
        resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
        print("Request successful!")
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)


def test_delete(url, filename):
    proxies = {"http": ""}
    payload = {"file_path": filename}
    try:
        resp = requests.post(url=url, json=payload, proxies=proxies)
        print(resp.text)
        resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
        print("Request successful!")
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)


def test_get(url):
    proxies = {"http": ""}
    try:
        resp = requests.post(url=url, proxies=proxies)
        print(resp.text)
        resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
        print("Request successful!")
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--test_option", type=str, default="ingest", help="ingest, get, delete")
    parser.add_argument("--port", type=str, default="6007", help="port number")
    args = parser.parse_args()

    port = args.port

    if args.test_option == "ingest":
        url = f"http://localhost:{port}/v1/dataprep/ingest"
        link_list = [
            "https://www.fool.com/earnings/call-transcripts/2025/03/06/costco-wholesale-cost-q2-2025-earnings-call-transc/",
            "https://www.fool.com/earnings/call-transcripts/2025/03/07/gap-gap-q4-2024-earnings-call-transcript/",
        ]
        test_html(url, link_list)
    elif args.test_option == "delete":
        url = f"http://localhost:{port}/v1/dataprep/delete"
        filename = "Costco Wholesale"
        test_delete(url, filename)
    elif args.test_option == "get":
        url = f"http://localhost:{port}/v1/dataprep/get"
        test_get(url)
    else:
        raise ValueError("Invalid test_option value. Please choose from ingest, get, delete.")

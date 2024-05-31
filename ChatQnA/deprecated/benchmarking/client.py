#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#

import argparse
import concurrent.futures
import json
import random

import requests


def extract_qText(json_data):
    try:
        file = open("devtest.json")
        data = json.load(file)
        json_data = json.loads(json_data)
        json_data["inputs"] = data[random.randint(0, len(data) - 1)]["qText"]
        return json.dumps(json_data)
    except (json.JSONDecodeError, KeyError, IndexError):
        return None


def send_request(url, json_data):
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json_data, headers=headers)
    print(f"Question: {json_data} Response: {response.status_code} - {response.text}")


def main(url, json_data, concurrency):
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_url = {
            executor.submit(send_request, url, extract_qText(json_data)): url for _ in range(concurrency * 2)
        }
        for future in concurrent.futures.as_completed(future_to_url):
            _ = future_to_url[future]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Concurrent client to send POST requests")
    parser.add_argument("--url", type=str, default="http://localhost:12345", help="URL to send requests to")
    parser.add_argument(
        "--json_data",
        type=str,
        default='{"inputs":"Which NFL team won the Super Bowl in the 2010 season?","parameters":{"do_sample": true}}',
        help="JSON data to send",
    )
    parser.add_argument("--concurrency", type=int, default=100, help="Concurrency level")
    args = parser.parse_args()
    main(args.url, args.json_data, args.concurrency)

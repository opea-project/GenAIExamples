# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os

import requests

ip_address = os.environ.get("ip_address")
endpoint = f"http://{ip_address}:9066/v1/animation"
outfile = os.environ.get("OUTFILE")

# Read the JSON file
with open("comps/animation/wav2lip/assets/audio/sample_question.json", "r") as file:
    data = json.load(file)

response = requests.post(url=endpoint, json=data, headers={"Content-Type": "application/json"}, proxies={"http": None})
print(f"Status code: {response.status_code}")
if response.status_code == 200:
    print(f"Check {outfile} for the result.")
print(response.json())

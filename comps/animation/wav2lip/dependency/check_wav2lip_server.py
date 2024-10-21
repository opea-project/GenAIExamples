# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os

import requests

endpoint = "http://localhost:7860/v1/wav2lip"
outfile = os.environ.get("OUTFILE")

# Read the JSON file
with open("assets/audio/sample_question.json", "r") as file:
    data = json.load(file)

inputs = {"audio": data["byte_str"]}
response = requests.post(url=endpoint, data=json.dumps(inputs), proxies={"http": None})
print(response.json())

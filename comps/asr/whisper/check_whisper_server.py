# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import json
import os
import urllib.request
import uuid
from io import BytesIO

import requests

# https://gist.github.com/novwhisky/8a1a0168b94f3b6abfaa
# test_audio_base64_str = "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"

uid = str(uuid.uuid4())
file_name = uid + ".wav"

urllib.request.urlretrieve(
    "https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample.wav",
    file_name,
)

with open(file_name, "rb") as f:
    test_audio_base64_str = base64.b64encode(f.read()).decode("utf-8")
os.remove(file_name)

endpoint = "http://localhost:7066/v1/asr"
inputs = {"audio": test_audio_base64_str}
response = requests.post(url=endpoint, data=json.dumps(inputs), proxies={"http": None})
print(response.json())

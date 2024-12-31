# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import json
import os
import urllib.request
import uuid

import requests

# https://gist.github.com/novwhisky/8a1a0168b94f3b6abfaa
# test_audio_base64_str = "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"

uid = str(uuid.uuid4())
file_name = uid + ".wav"

urllib.request.urlretrieve(
    "https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample.wav",
    file_name,
)

endpoint = "http://localhost:9099/v1/audio/transcriptions"
headers = {"accept": "application/json"}

# Prepare the data and files
data = {
    "model": "openai/whisper-small",
    "language": "english",
}

try:
    with open(file_name, "rb") as audio_file:
        files = {"file": (file_name, audio_file)}
        response = requests.post(endpoint, headers=headers, data=data, files=files)
        if response.status_code != 200:
            print(f"Failure with {response.reason}!")
        else:
            print(response.json())
except Exception as e:
    print(f"Failure with {e}!")

os.remove(file_name)

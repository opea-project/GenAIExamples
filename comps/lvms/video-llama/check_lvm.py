# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import datetime
import json
import os

import requests

ip_address = os.getenv("ip_address")
####### video-llama request ########
print("video-llama request")
api_url = f"http://${ip_address}:9009/generate"
content = {
    "video_url": "https://github.com/DAMO-NLP-SG/Video-LLaMA/raw/main/examples/silence_girl.mp4",
    "start": 0.0,
    "duration": 9,
    "prompt": "What is the person doing?",
    "max_new_tokens": 150,
}

start = datetime.datetime.now()
with requests.post(api_url, params=content, stream=True) as response:
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            print(chunk.decode("utf-8"), end="", flush=True)  # Flush to ensure immediate output

end = datetime.datetime.now()
print(f"\nTotal time: {end - start}")

####### lvm request ########
print("lvm request")
api_url = f"http://${ip_address}:9000/v1/lvm"
headers = {"Content-Type": "application/json"}
data = {
    "video_url": "https://github.com/DAMO-NLP-SG/Video-LLaMA/raw/main/examples/silence_girl.mp4",
    "chunk_start": 0,
    "chunk_duration": 9,
    "prompt": "what is the person doing",
    "max_new_tokens": 150,
}

start = datetime.datetime.now()
with requests.post(api_url, headers=headers, data=json.dumps(data), stream=True) as response:
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            print(chunk.decode("utf-8"), end="", flush=True)  # Flush to ensure immediate output

end = datetime.datetime.now()
print(f"\nTotal time: {end - start}")

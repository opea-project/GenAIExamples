# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import base64
import json
from io import BytesIO

import PIL.Image
import requests

image_path = "https://avatars.githubusercontent.com/u/39623753?v=4"

image = PIL.Image.open(requests.get(image_path, stream=True, timeout=3000).raw)
buffered = BytesIO()
image.save(buffered, format="PNG")
img_b64_str = base64.b64encode(buffered.getvalue()).decode()

endpoint = "http://localhost:9399/v1/lvm"
inputs = {"image": img_b64_str, "prompt": "What is this?", "max_new_tokens": 32}
response = requests.post(url=endpoint, data=json.dumps(inputs), proxies={"http": None})
print(response.json())

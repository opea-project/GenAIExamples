# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from http import HTTPStatus

import httpx
import msgspec
import requests

input_text = "what a nice day"
req = {
    "query": input_text,
}

httpx_response = httpx.post("http://127.0.0.1:6001/inference", content=msgspec.msgpack.encode(req))

requests_response = requests.post("http://127.0.0.1:6001/inference", data=msgspec.msgpack.encode(req))

MOSEC_EMBEDDING_ENDPOINT = os.environ.get("MOSEC_EMBEDDING_ENDPOINT", "http://127.0.0.1:6001")

request_url = MOSEC_EMBEDDING_ENDPOINT + "/inference"
print(f"request_url = {request_url}")
resp_3 = requests.post(request_url, data=msgspec.msgpack.encode(req))

if httpx_response.status_code == HTTPStatus.OK and requests_response.status_code == HTTPStatus.OK:
    print(f"OK: \n {msgspec.msgpack.decode(httpx_response.content)}")
    print(f"OK: \n {msgspec.msgpack.decode(requests_response.content)}")
    print(f"OK: \n {msgspec.msgpack.decode(resp_3.content)}")
else:
    print(f"err[{httpx_response.status_code}] {httpx_response.text}")

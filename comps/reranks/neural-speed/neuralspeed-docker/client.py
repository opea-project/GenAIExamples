# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from http import HTTPStatus

import httpx
import msgspec
import requests

req = {
    "query": "talk is cheap, show me the code",
    "docs": [
        "what a nice day",
        "life is short, use python",
        "early bird catches the worm",
    ],
}

httpx_response = httpx.post("http://127.0.0.1:8080/inference", content=msgspec.msgpack.encode(req))

requests_response = requests.post("http://127.0.0.1:8080/inference", data=msgspec.msgpack.encode(req))

MOSEC_RERANKING_ENDPOINT = os.environ.get("MOSEC_RERANKING_ENDPOINT", "http://127.0.0.1:8080")

request_url = MOSEC_RERANKING_ENDPOINT + "/inference"
print(f"request_url = {request_url}")
resp_3 = requests.post(request_url, data=msgspec.msgpack.encode(req))

if httpx_response.status_code == HTTPStatus.OK and requests_response.status_code == HTTPStatus.OK:
    print(f"OK: \n {msgspec.msgpack.decode(httpx_response.content)}")
    print(f"OK: \n {msgspec.msgpack.decode(requests_response.content)}")
    print(f"OK: \n {msgspec.msgpack.decode(resp_3.content)}")
else:
    print(f"err[{httpx_response.status_code}] {httpx_response.text}")

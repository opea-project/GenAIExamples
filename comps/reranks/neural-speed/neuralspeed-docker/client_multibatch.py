# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
from threading import Thread

import httpx
import msgspec

req = {
    "query": "talk is cheap, show me the code",
    "docs": [
        "what a nice day",
        "life is short, use python",
        "early bird catches the worm",
    ],
}
reqs = []
BATCH = 32
for i in range(BATCH):
    reqs.append(msgspec.msgpack.encode(req))


def post_func(threadIdx):
    resp = httpx.post("http://127.0.0.1:8080/inference", content=reqs[threadIdx])
    ret = f"thread {threadIdx} \n"
    if resp.status_code == HTTPStatus.OK:
        ret += f"OK: {msgspec.msgpack.decode(resp.content)['scores']}"
    else:
        ret += f"err[{resp.status_code}] {resp.text}"
    print(ret)


threads = []
for i in range(BATCH):
    t = Thread(
        target=post_func,
        args=[
            i,
        ],
    )
    threads.append(t)

for i in range(BATCH):
    threads[i].start()

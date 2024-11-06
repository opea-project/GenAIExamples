# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import unittest
from enum import Enum

import aiohttp

from comps import ServiceType, TextDoc, opea_microservices, register_microservice


async def dynamic_batching_infer(service_type: Enum, batch: list[dict]):
    # simulate batch inference time
    asyncio.sleep(5)
    assert len(batch) == 2
    return [{"result": "processed: " + i["request"].text} for i in batch]


@register_microservice(
    name="s1",
    host="0.0.0.0",
    port=8080,
    endpoint="/v1/add1",
    dynamic_batching=True,
    dynamic_batching_timeout=2,
    dynamic_batching_max_batch_size=32,
)
async def add(request: TextDoc) -> dict:
    response_future = asyncio.get_event_loop().create_future()

    cur_microservice = opea_microservices["s1"]
    cur_microservice.dynamic_batching_infer = dynamic_batching_infer

    async with cur_microservice.buffer_lock:
        cur_microservice.request_buffer[ServiceType.EMBEDDING].append({"request": request, "response": response_future})
    result = await response_future
    return result


@register_microservice(
    name="s1",
    host="0.0.0.0",
    port=8080,
    endpoint="/v1/add2",
    dynamic_batching=True,
    dynamic_batching_timeout=3,
    dynamic_batching_max_batch_size=32,
)
async def add2(request: TextDoc) -> dict:
    response_future = asyncio.get_event_loop().create_future()

    cur_microservice = opea_microservices["s1"]
    cur_microservice.dynamic_batching_infer = dynamic_batching_infer

    async with cur_microservice.buffer_lock:
        cur_microservice.request_buffer[ServiceType.EMBEDDING].append({"request": request, "response": response_future})
    result = await response_future
    return result


async def fetch(session, url, data):
    async with session.post(url, json=data) as response:
        # Await the response and return the JSON data
        return await response.json()


class TestMicroService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        opea_microservices["s1"].start()

    def tearDown(self):
        opea_microservices["s1"].stop()

    async def test_dynamic_batching(self):
        url1 = "http://localhost:8080/v1/add1"
        url2 = "http://localhost:8080/v1/add2"

        # Data for the requests
        data1 = {"text": "Hello, "}
        data2 = {"text": "OPEA Project!"}

        async with aiohttp.ClientSession() as session:
            response1, response2 = await asyncio.gather(fetch(session, url1, data1), fetch(session, url2, data2))

        self.assertEqual(response1["result"], "processed: Hello, ")
        self.assertEqual(response2["result"], "processed: OPEA Project!")


if __name__ == "__main__":
    unittest.main()

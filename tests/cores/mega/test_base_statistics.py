# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import time
import unittest

import requests

from comps import (
    ServiceOrchestrator,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)


@register_microservice(name="s1", host="0.0.0.0", port=8083, endpoint="/v1/add")
@register_statistics(names=["opea_service@s1_add"])
async def s1_add(request: TextDoc) -> TextDoc:
    start = time.time()
    time.sleep(5)
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "opea"
    statistics_dict["opea_service@s1_add"].append_latency(time.time() - start, None)
    return {"text": text}


class TestBaseStatistics(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.s1 = opea_microservices["s1"]
        self.s1.start()

        self.service_builder = ServiceOrchestrator()
        self.service_builder.add(opea_microservices["s1"])

    def tearDown(self):
        self.s1.stop()

    async def test_base_statistics(self):
        for _ in range(2):
            task1 = asyncio.create_task(self.service_builder.schedule(initial_inputs={"text": "hello, "}))
            await asyncio.gather(task1)
            result_dict1, _ = task1.result()

        response = requests.get("http://localhost:8083/v1/statistics")
        res = response.json()
        p50 = res["opea_service@s1_add"]["p50_latency"]
        p99 = res["opea_service@s1_add"]["p99_latency"]
        self.assertEqual(int(p50), int(p99))


if __name__ == "__main__":
    unittest.main()

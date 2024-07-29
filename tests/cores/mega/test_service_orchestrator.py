# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

from comps import ServiceOrchestrator, TextDoc, opea_microservices, register_microservice


@register_microservice(name="s1", host="0.0.0.0", port=8083, endpoint="/v1/add")
async def s1_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "opea "
    return {"text": text}


@register_microservice(name="s2", host="0.0.0.0", port=8084, endpoint="/v1/add")
async def s2_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "project!"
    return {"text": text}


class TestServiceOrchestrator(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.s1 = opea_microservices["s1"]
        cls.s2 = opea_microservices["s2"]
        cls.s1.start()
        cls.s2.start()

        cls.service_builder = ServiceOrchestrator()

        cls.service_builder.add(opea_microservices["s1"]).add(opea_microservices["s2"])
        cls.service_builder.flow_to(cls.s1, cls.s2)

    @classmethod
    def tearDownClass(cls):
        cls.s1.stop()
        cls.s2.stop()

    async def test_schedule(self):
        result_dict, _ = await self.service_builder.schedule(initial_inputs={"text": "hello, "})
        self.assertEqual(result_dict[self.s2.name]["text"], "hello, opea project!")


if __name__ == "__main__":
    unittest.main()

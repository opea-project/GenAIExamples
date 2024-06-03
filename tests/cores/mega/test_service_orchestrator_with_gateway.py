# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

from comps import Gateway, ServiceOrchestrator, TextDoc, opea_microservices, register_microservice


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
    def setUp(self):
        self.s1 = opea_microservices["s1"]
        self.s2 = opea_microservices["s2"]
        self.s1.start()
        self.s2.start()

        self.service_builder = ServiceOrchestrator()

        self.service_builder.add(opea_microservices["s1"]).add(opea_microservices["s2"])
        self.service_builder.flow_to(self.s1, self.s2)
        self.gateway = Gateway(self.service_builder, port=9898)

    def tearDown(self):
        self.s1.stop()
        self.s2.stop()
        self.gateway.stop()

    async def test_schedule(self):
        result_dict = await self.service_builder.schedule(initial_inputs={"text": "hello, "})
        self.assertEqual(result_dict[self.s2.name]["text"], "hello, opea project!")


if __name__ == "__main__":
    unittest.main()

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

from comps import ServiceOrchestratorWithYaml, TextDoc, opea_microservices, register_microservice


@register_microservice(name="s1", host="0.0.0.0", port=8081, endpoint="/v1/add")
async def s1_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "opea "
    return {"text": text}


@register_microservice(name="s2", host="0.0.0.0", port=8082, endpoint="/v1/add")
async def s2_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "project!"
    return {"text": text}


class TestYAMLOrchestrator(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.s1 = opea_microservices["s1"]
        self.s2 = opea_microservices["s2"]
        self.s1.start()
        self.s2.start()

    def tearDown(self):
        self.s1.stop()
        self.s2.stop()

    async def test_schedule(self):
        service_builder = ServiceOrchestratorWithYaml(yaml_file_path="megaservice.yaml")
        await service_builder.schedule(initial_inputs={"text": "Hello, "})
        result_dict = service_builder.result_dict
        self.assertEqual(result_dict["s2"]["text"], "Hello, opea project!")


if __name__ == "__main__":
    unittest.main()

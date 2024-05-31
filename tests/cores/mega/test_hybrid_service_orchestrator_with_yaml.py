# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

from comps import ServiceOrchestratorWithYaml, TextDoc, opea_microservices, register_microservice


@register_microservice(name="s1", host="0.0.0.0", port=8085, endpoint="/v1/add")
async def s1_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "opea "
    return {"text": text}


class TestYAMLOrchestrator(unittest.TestCase):
    def setUp(self) -> None:
        self.s1 = opea_microservices["s1"]
        self.s1.start()

    def tearDown(self):
        self.s1.stop()

    def test_add_remote_service(self):
        service_builder = ServiceOrchestratorWithYaml(yaml_file_path="megaservice_hybrid.yaml")
        self.assertEqual(service_builder.all_leaves()[0], "s2")
        self.assertEqual(service_builder.docs["opea_micro_services"]["s2"]["endpoint"], "http://fakehost:8008/v1/add")


if __name__ == "__main__":
    unittest.main()

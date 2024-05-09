# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import unittest

from comps import ServiceOrchestratorWithYaml, TextDoc, opea_microservices, register_microservice


@register_microservice(name="s1", port=8081, expose_endpoint="/v1/add")
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
        service_builder = ServiceOrchestratorWithYaml(yaml_file_path="./megaservice_hybrid.yaml")
        self.assertEqual(service_builder.all_leaves()[0], "s2")
        self.assertEqual(service_builder.docs["opea_micro_services"]["s2"]["endpoint"], "http://fakehost:8008/v1/add")


if __name__ == "__main__":
    unittest.main()

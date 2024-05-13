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


@register_microservice(name="s1", host="0.0.0.0", port=8081, expose_endpoint="/v1/add")
async def s1_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "opea "
    return {"text": text}


@register_microservice(name="s2", host="0.0.0.0", port=8082, expose_endpoint="/v1/add")
async def s2_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "project!"
    return {"text": text}


class TestYAMLOrchestrator(unittest.TestCase):
    def setUp(self) -> None:
        self.s1 = opea_microservices["s1"]
        self.s2 = opea_microservices["s2"]
        self.s1.start()
        self.s2.start()

    def tearDown(self):
        self.s1.stop()
        self.s2.stop()

    def test_schedule(self):
        service_builder = ServiceOrchestratorWithYaml(yaml_file_path="megaservice.yaml")
        service_builder.schedule(initial_inputs={"text": "Hello, "})
        service_builder.get_all_final_outputs()
        result_dict = service_builder.result_dict
        self.assertEqual(result_dict["s2"]["text"], "Hello, opea project!")


if __name__ == "__main__":
    unittest.main()

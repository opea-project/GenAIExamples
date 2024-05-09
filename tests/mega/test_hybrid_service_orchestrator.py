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

from comps import RemoteMicroService, ServiceOrchestrator, TextDoc, opea_microservices, register_microservice


@register_microservice(name="s1", host="0.0.0.0", port=8086, expose_endpoint="/v1/add")
async def s1_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "opea "
    return {"text": text}


class TestServiceOrchestrator(unittest.TestCase):
    def setUp(self):
        self.s1 = opea_microservices["s1"]
        self.s1.start()

        self.service_builder = ServiceOrchestrator(port=8000, hostfile=None)

    def tearDown(self):
        self.s1.stop()

    def test_add_remote_service(self):
        s2 = RemoteMicroService(name="s2", host="fakehost", port=8008, expose_endpoint="/v1/add")
        self.service_builder.add(opea_microservices["s1"]).add(s2)
        self.service_builder.flow_to(self.s1, s2)
        self.assertEqual(s2.endpoint_path, "http://fakehost:8008/v1/add")


if __name__ == "__main__":
    unittest.main()

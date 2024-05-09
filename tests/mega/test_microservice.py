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

from fastapi.testclient import TestClient

from comps import TextDoc, opea_microservices, register_microservice


@register_microservice(name="s1", host="0.0.0.0", port=8080, expose_endpoint="/v1/add")
async def add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "OPEA Project!"
    return {"text": text}


class TestMicroService(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(opea_microservices["s1"].app)

        opea_microservices["s1"].start()

    def tearDown(self):
        opea_microservices["s1"].stop()

    def test_add_route(self):
        response = self.client.post("/v1/add", json={"text": "Hello, "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "Hello, OPEA Project!")


if __name__ == "__main__":
    unittest.main()

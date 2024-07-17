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

import asyncio
import json
import time
import unittest

from comps import ServiceOrchestrator, TextDoc, opea_microservices, register_microservice


@register_microservice(name="s1", host="0.0.0.0", port=8083, endpoint="/v1/add")
async def s1_add(request: TextDoc) -> TextDoc:
    time.sleep(5)
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "opea"
    return {"text": text}


@register_microservice(name="s2", host="0.0.0.0", port=8084, endpoint="/v1/add")
async def s2_add(request: TextDoc) -> TextDoc:
    time.sleep(5)
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += " project1!"
    return {"text": text}


@register_microservice(name="s3", host="0.0.0.0", port=8085, endpoint="/v1/add")
async def s3_add(request: TextDoc) -> TextDoc:
    time.sleep(5)
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += " project2!"
    return {"text": text}


class TestServiceOrchestrator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.s1 = opea_microservices["s1"]
        self.s2 = opea_microservices["s2"]
        self.s3 = opea_microservices["s3"]
        self.s1.start()
        self.s2.start()
        self.s3.start()

        self.service_builder = ServiceOrchestrator()

        self.service_builder.add(opea_microservices["s1"]).add(opea_microservices["s2"]).add(opea_microservices["s3"])
        self.service_builder.flow_to(self.s1, self.s2)
        self.service_builder.flow_to(self.s1, self.s3)

    def tearDown(self):
        self.s1.stop()
        self.s2.stop()
        self.s3.stop()

    async def test_schedule(self):
        t = time.time()
        task1 = asyncio.create_task(self.service_builder.schedule(initial_inputs={"text": "hello, "}))
        task2 = asyncio.create_task(self.service_builder.schedule(initial_inputs={"text": "hi, "}))
        await asyncio.gather(task1, task2)

        result_dict1, runtime_graph1 = task1.result()
        result_dict2, runtime_graph2 = task2.result()
        self.assertEqual(result_dict1[self.s2.name]["text"], "hello, opea project1!")
        self.assertEqual(result_dict1[self.s3.name]["text"], "hello, opea project2!")
        self.assertEqual(result_dict2[self.s2.name]["text"], "hi, opea project1!")
        self.assertEqual(result_dict2[self.s3.name]["text"], "hi, opea project2!")
        self.assertEqual(len(self.service_builder.get_all_final_outputs(result_dict1, runtime_graph1).keys()), 2)
        self.assertEqual(int(time.time() - t), 15)


if __name__ == "__main__":
    unittest.main()

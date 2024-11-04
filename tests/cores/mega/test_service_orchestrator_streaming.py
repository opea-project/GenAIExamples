# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import time
import unittest

from fastapi.responses import StreamingResponse

from comps import ServiceOrchestrator, ServiceType, TextDoc, opea_microservices, register_microservice


@register_microservice(name="s1", host="0.0.0.0", port=8083, endpoint="/v1/add")
async def s1_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += " ~~~"
    return {"text": text}


@register_microservice(name="s0", host="0.0.0.0", port=8085, endpoint="/v1/add", service_type=ServiceType.LLM)
async def s0_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]

    async def token_generator():
        for i in [" OPEA", " is", " great.", " I", " think ", " so."]:
            yield i

    text += "project!"
    return StreamingResponse(token_generator(), media_type="text/event-stream")


class TestServiceOrchestratorStreaming(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.s0 = opea_microservices["s0"]
        cls.s1 = opea_microservices["s1"]
        cls.s0.start()
        cls.s1.start()

        cls.service_builder = ServiceOrchestrator()

        cls.service_builder.add(opea_microservices["s0"]).add(opea_microservices["s1"])
        cls.service_builder.flow_to(cls.s0, cls.s1)

    @classmethod
    def tearDownClass(cls):
        cls.s0.stop()
        cls.s1.stop()

    async def test_schedule(self):
        result_dict, _ = await self.service_builder.schedule(initial_inputs={"text": "hello, "})
        response = result_dict["s1/MicroService"]
        idx = 0
        res_expected = ["OPEA", "is", "great.", "~~~", "I", "think", "so.", "~~~"]
        async for k in response.__reduce__()[2]["body_iterator"]:
            self.assertEqual(self.service_builder.extract_chunk_str(k).strip(), res_expected[idx])
            idx += 1

    def test_extract_chunk_str(self):
        res = self.service_builder.extract_chunk_str("data: [DONE]\n\n")
        self.assertEqual(res, "")
        res = self.service_builder.extract_chunk_str("data: b'example test.'\n\n")
        self.assertEqual(res, "example test.")

    def test_token_generator(self):
        start = time.time()
        sentence = "I write an example test.</s>"
        for i in self.service_builder.token_generator(
            sentence=sentence, token_start=start, is_first=True, is_last=False
        ):
            self.assertTrue(i.startswith("data: b'"))

        for i in self.service_builder.token_generator(
            sentence=sentence, token_start=start, is_first=False, is_last=True
        ):
            self.assertTrue(i.startswith("data: "))


if __name__ == "__main__":
    unittest.main()

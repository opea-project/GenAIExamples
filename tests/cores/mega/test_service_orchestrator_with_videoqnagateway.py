# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

from fastapi.responses import StreamingResponse

from comps import ServiceOrchestrator, ServiceType, TextDoc, VideoQnAGateway, opea_microservices, register_microservice
from comps.cores.proto.docarray import LLMParams


@register_microservice(name="s1", host="0.0.0.0", port=8083, endpoint="/v1/add")
async def s1_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "opea "
    return {"text": text}


@register_microservice(name="s2", host="0.0.0.0", port=8084, endpoint="/v1/add", service_type=ServiceType.LVM)
async def s2_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]

    def streamer(text):
        yield f"{text}".encode("utf-8")
        for i in range(3):
            yield "project!".encode("utf-8")

    return StreamingResponse(streamer(text), media_type="text/event-stream")


class TestServiceOrchestrator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.s1 = opea_microservices["s1"]
        self.s2 = opea_microservices["s2"]
        self.s1.start()
        self.s2.start()

        self.service_builder = ServiceOrchestrator()

        self.service_builder.add(opea_microservices["s1"]).add(opea_microservices["s2"])
        self.service_builder.flow_to(self.s1, self.s2)
        self.gateway = VideoQnAGateway(self.service_builder, port=9898)

    def tearDown(self):
        self.s1.stop()
        self.s2.stop()
        self.gateway.stop()

    async def test_schedule(self):
        result_dict, _ = await self.service_builder.schedule(
            initial_inputs={"text": "hello, "}, llm_parameters=LLMParams(streaming=True)
        )
        streaming_response = result_dict[self.s2.name]

        if isinstance(streaming_response, StreamingResponse):
            content = b""
            async for chunk in streaming_response.body_iterator:
                content += chunk
            final_text = content.decode("utf-8")

        print("Streamed content from s2: ", final_text)

        expected_result = "hello, opea project!project!project!"
        self.assertEqual(final_text, expected_result)


if __name__ == "__main__":
    unittest.main()

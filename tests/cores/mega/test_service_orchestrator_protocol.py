# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import unittest

from comps import ServiceOrchestrator, opea_microservices, register_microservice
from comps.cores.proto.api_protocol import ChatCompletionRequest


@register_microservice(name="s1", host="0.0.0.0", port=8083, endpoint="/v1/add")
async def s1_add(request: ChatCompletionRequest) -> ChatCompletionRequest:
    # support pydantic protocol message object in/out in data flow
    return request


class TestServiceOrchestratorProtocol(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.s1 = opea_microservices["s1"]
        self.s1.start()

        self.service_builder = ServiceOrchestrator()

        self.service_builder.add(opea_microservices["s1"])

    def tearDown(self):
        self.s1.stop()

    async def test_schedule(self):
        input_data = ChatCompletionRequest(messages=[{"role": "user", "content": "What's up man?"}], seed=None)
        result_dict, _ = await self.service_builder.schedule(initial_inputs=input_data)
        self.assertEqual(
            result_dict[self.s1.name]["messages"],
            [{"role": "user", "content": "What's up man?"}],
        )
        self.assertEqual(result_dict[self.s1.name]["seed"], None)


if __name__ == "__main__":
    unittest.main()

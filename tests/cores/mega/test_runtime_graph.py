# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

from fastapi.testclient import TestClient

from comps import ServiceOrchestrator, TextDoc, opea_microservices, register_microservice


@register_microservice(name="s1", host="0.0.0.0", port=8080, endpoint="/v1/add")
async def add_s1(request: TextDoc) -> TextDoc:
    text = request.text
    if "Hi" in text:
        text += "OPEA Project!"
        return TextDoc(text=text, downstream_black_list=[])
    elif "Bye" in text:
        text += "OPEA Project!"
        return TextDoc(text=text, downstream_black_list=[".*"])
    elif "Hola" in text:
        text += "OPEA Project!"
        return TextDoc(text=text, downstream_black_list=["s2"])
    else:
        text += "OPEA Project!"
        return TextDoc(text=text, downstream_black_list=["s3"])


@register_microservice(name="s2", host="0.0.0.0", port=8081, endpoint="/v1/add")
async def add_s2(request: TextDoc) -> TextDoc:
    text = request.text
    text += "add s2!"
    return TextDoc(text=text)


@register_microservice(name="s3", host="0.0.0.0", port=8082, endpoint="/v1/add")
async def add_s3(request: TextDoc) -> TextDoc:
    text = request.text
    text += "add s3!"
    return TextDoc(text=text)


@register_microservice(name="s4", host="0.0.0.0", port=8083, endpoint="/v1/add")
async def add_s4(request: TextDoc) -> TextDoc:
    text = request.text
    text += "add s4!"
    return TextDoc(text=text)


class TestMicroService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client1 = TestClient(opea_microservices["s1"].app)
        self.s1 = opea_microservices["s1"]
        self.s2 = opea_microservices["s2"]
        self.s3 = opea_microservices["s3"]
        self.s4 = opea_microservices["s4"]

        self.s1.start()
        self.s2.start()
        self.s3.start()
        self.s4.start()

        self.service_builder = ServiceOrchestrator()
        self.service_builder.add(self.s1).add(self.s2).add(self.s3).add(self.s4)
        self.service_builder.flow_to(self.s1, self.s2)
        self.service_builder.flow_to(self.s1, self.s3)
        self.service_builder.flow_to(self.s3, self.s4)

    def tearDown(self):
        self.s1.stop()
        self.s2.stop()
        self.s3.stop()
        self.s4.stop()

    async def test_add_route(self):
        result_dict, runtime_graph = await self.service_builder.schedule(initial_inputs={"text": "Hi!"})
        assert len(result_dict) == 4
        assert len(runtime_graph.all_leaves()) == 2
        result_dict, runtime_graph = await self.service_builder.schedule(initial_inputs={"text": "Bye!"})
        assert len(result_dict) == 1
        assert len(runtime_graph.all_leaves()) == 1
        result_dict, runtime_graph = await self.service_builder.schedule(initial_inputs={"text": "Hola!"})
        assert len(result_dict) == 3
        assert len(runtime_graph.all_leaves()) == 1
        result_dict, runtime_graph = await self.service_builder.schedule(initial_inputs={"text": "Other!"})
        print(runtime_graph.graph)
        assert len(result_dict) == 2
        assert len(runtime_graph.all_leaves()) == 1


if __name__ == "__main__":
    unittest.main()

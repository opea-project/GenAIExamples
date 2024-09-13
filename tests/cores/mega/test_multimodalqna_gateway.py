# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from typing import Union

import requests
from fastapi import Request

from comps import (
    EmbedDoc,
    EmbedMultimodalDoc,
    LVMDoc,
    LVMSearchedMultimodalDoc,
    MultimodalDoc,
    MultimodalQnAGateway,
    SearchedMultimodalDoc,
    ServiceOrchestrator,
    TextDoc,
    opea_microservices,
    register_microservice,
)


@register_microservice(name="mm_embedding", host="0.0.0.0", port=8083, endpoint="/v1/mm_embedding")
async def mm_embedding_add(request: MultimodalDoc) -> EmbedDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    res = {}
    res["text"] = text
    res["embedding"] = [0.12, 0.45]
    return res


@register_microservice(name="mm_retriever", host="0.0.0.0", port=8084, endpoint="/v1/mm_retriever")
async def mm_retriever_add(request: EmbedMultimodalDoc) -> SearchedMultimodalDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    res = {}
    res["retrieved_docs"] = []
    res["initial_query"] = text
    res["top_n"] = 1
    res["metadata"] = [
        {
            "b64_img_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC",
            "transcript_for_inference": "yellow image",
        }
    ]
    res["chat_template"] = "The caption of the image is: '{context}'. {question}"
    return res


@register_microservice(name="lvm", host="0.0.0.0", port=8085, endpoint="/v1/lvm")
async def lvm_add(request: Union[LVMDoc, LVMSearchedMultimodalDoc]) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    if isinstance(request, LVMSearchedMultimodalDoc):
        print("request is the output of multimodal retriever")
        text = req_dict["initial_query"]
        text += "opea project!"

    else:
        print("request is from user.")
        text = req_dict["prompt"]
        text = f"<image>\nUSER: {text}\nASSISTANT:"

    res = {}
    res["text"] = text
    return res


class TestServiceOrchestrator(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.mm_embedding = opea_microservices["mm_embedding"]
        cls.mm_retriever = opea_microservices["mm_retriever"]
        cls.lvm = opea_microservices["lvm"]
        cls.mm_embedding.start()
        cls.mm_retriever.start()
        cls.lvm.start()

        cls.service_builder = ServiceOrchestrator()

        cls.service_builder.add(opea_microservices["mm_embedding"]).add(opea_microservices["mm_retriever"]).add(
            opea_microservices["lvm"]
        )
        cls.service_builder.flow_to(cls.mm_embedding, cls.mm_retriever)
        cls.service_builder.flow_to(cls.mm_retriever, cls.lvm)

        cls.follow_up_query_service_builder = ServiceOrchestrator()
        cls.follow_up_query_service_builder.add(cls.lvm)

        cls.gateway = MultimodalQnAGateway(cls.service_builder, cls.follow_up_query_service_builder, port=9898)

    @classmethod
    def tearDownClass(cls):
        cls.mm_embedding.stop()
        cls.mm_retriever.stop()
        cls.lvm.stop()
        cls.gateway.stop()

    async def test_service_builder_schedule(self):
        result_dict, _ = await self.service_builder.schedule(initial_inputs={"text": "hello, "})
        self.assertEqual(result_dict[self.lvm.name]["text"], "hello, opea project!")

    async def test_follow_up_query_service_builder_schedule(self):
        result_dict, _ = await self.follow_up_query_service_builder.schedule(
            initial_inputs={"prompt": "chao, ", "image": "some image"}
        )
        # print(result_dict)
        self.assertEqual(result_dict[self.lvm.name]["text"], "<image>\nUSER: chao, \nASSISTANT:")

    def test_MultimodalQnAGateway_gateway(self):
        json_data = {"messages": "hello, "}
        response = requests.post("http://0.0.0.0:9898/v1/multimodalqna", json=json_data)
        response = response.json()
        self.assertEqual(response["choices"][-1]["message"]["content"], "hello, opea project!")

    def test_follow_up_MultimodalQnAGateway_gateway(self):
        json_data = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "hello, "},
                        {
                            "type": "image_url",
                            "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"},
                        },
                    ],
                },
                {"role": "assistant", "content": "opea project! "},
                {"role": "user", "content": "chao, "},
            ],
            "max_tokens": 300,
        }
        response = requests.post("http://0.0.0.0:9898/v1/multimodalqna", json=json_data)
        response = response.json()
        self.assertEqual(
            response["choices"][-1]["message"]["content"],
            "<image>\nUSER: hello, \nASSISTANT: opea project! \nUSER: chao, \n\nASSISTANT:",
        )

    def test_handle_message(self):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "hello, "},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"},
                    },
                ],
            },
            {"role": "assistant", "content": "opea project! "},
            {"role": "user", "content": "chao, "},
        ]
        prompt, images = self.gateway._handle_message(messages)
        self.assertEqual(prompt, "hello, \nASSISTANT: opea project! \nUSER: chao, \n")

    def test_handle_message_with_system_prompt(self):
        messages = [
            {"role": "system", "content": "System Prompt"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "hello, "},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"},
                    },
                ],
            },
            {"role": "assistant", "content": "opea project! "},
            {"role": "user", "content": "chao, "},
        ]
        prompt, images = self.gateway._handle_message(messages)
        self.assertEqual(prompt, "System Prompt\nhello, \nASSISTANT: opea project! \nUSER: chao, \n")

    async def test_handle_request(self):
        json_data = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "hello, "},
                        {
                            "type": "image_url",
                            "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"},
                        },
                    ],
                },
                {"role": "assistant", "content": "opea project! "},
                {"role": "user", "content": "chao, "},
            ],
            "max_tokens": 300,
        }
        mock_request = Request(scope={"type": "http"})
        mock_request._json = json_data
        res = await self.gateway.handle_request(mock_request)
        res = json.loads(res.json())
        self.assertEqual(
            res["choices"][-1]["message"]["content"],
            "<image>\nUSER: hello, \nASSISTANT: opea project! \nUSER: chao, \n\nASSISTANT:",
        )


if __name__ == "__main__":
    unittest.main()

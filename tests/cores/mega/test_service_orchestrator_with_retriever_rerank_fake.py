# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

from comps import (
    EmbedDoc,
    Gateway,
    RerankedDoc,
    ServiceOrchestrator,
    TextDoc,
    opea_microservices,
    register_microservice,
)
from comps.cores.mega.constants import ServiceType
from comps.cores.proto.docarray import LLMParams, RerankerParms, RetrieverParms


@register_microservice(name="s1", host="0.0.0.0", port=8083, endpoint="/v1/add", service_type=ServiceType.RETRIEVER)
async def s1_add(request: EmbedDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += f"opea top_k {req_dict['k']}"
    return {"text": text}


@register_microservice(name="s2", host="0.0.0.0", port=8084, endpoint="/v1/add", service_type=ServiceType.RERANK)
async def s2_add(request: TextDoc) -> TextDoc:
    req = request.model_dump_json()
    req_dict = json.loads(req)
    text = req_dict["text"]
    text += "project!"
    return {"text": text}


def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs):
    if self.services[cur_node].service_type == ServiceType.RETRIEVER:
        inputs["k"] = kwargs["retriever_parameters"].k

    return inputs


def align_outputs(self, outputs, cur_node, inputs, runtime_graph, llm_parameters_dict, **kwargs):
    if self.services[cur_node].service_type == ServiceType.RERANK:
        top_n = kwargs["reranker_parameters"].top_n
        outputs["text"] = outputs["text"][:top_n]
    return outputs


class TestServiceOrchestratorParams(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.s1 = opea_microservices["s1"]
        self.s2 = opea_microservices["s2"]
        self.s1.start()
        self.s2.start()

        ServiceOrchestrator.align_inputs = align_inputs
        ServiceOrchestrator.align_outputs = align_outputs
        self.service_builder = ServiceOrchestrator()

        self.service_builder.add(opea_microservices["s1"]).add(opea_microservices["s2"])
        self.service_builder.flow_to(self.s1, self.s2)
        self.gateway = Gateway(self.service_builder, port=9898)

    def tearDown(self):
        self.s1.stop()
        self.s2.stop()
        self.gateway.stop()

    async def test_retriever_schedule(self):
        result_dict, _ = await self.service_builder.schedule(
            initial_inputs={"text": "hello, ", "embedding": [1.0, 2.0, 3.0]},
            retriever_parameters=RetrieverParms(k=8),
            reranker_parameters=RerankerParms(top_n=20),
        )
        self.assertEqual(len(result_dict[self.s2.name]["text"]), 20)  # Check reranker top_n is accessed
        self.assertTrue("8" in result_dict[self.s2.name]["text"])  # Check retriever k is accessed


if __name__ == "__main__":
    unittest.main()

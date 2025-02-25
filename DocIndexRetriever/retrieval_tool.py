# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import asyncio
import os
from typing import Union

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.proto.api_protocol import ChatCompletionRequest, EmbeddingRequest
from comps.cores.proto.docarray import LLMParamsDoc, RerankedDoc, RerankerParms, RetrieverParms, TextDoc
from fastapi import Request
from fastapi.responses import StreamingResponse

MEGA_SERVICE_PORT = os.getenv("MEGA_SERVICE_PORT", 8889)
EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)
RETRIEVER_SERVICE_HOST_IP = os.getenv("RETRIEVER_SERVICE_HOST_IP", "0.0.0.0")
RETRIEVER_SERVICE_PORT = os.getenv("RETRIEVER_SERVICE_PORT", 7000)
RERANK_SERVICE_HOST_IP = os.getenv("RERANK_SERVICE_HOST_IP", "0.0.0.0")
RERANK_SERVICE_PORT = os.getenv("RERANK_SERVICE_PORT", 8000)


def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs):
    print(f"Inputs to {cur_node}: {inputs}")
    for key, value in kwargs.items():
        print(f"{key}: {value}")
    return inputs


def align_outputs(self, data, cur_node, inputs, runtime_graph, llm_parameters_dict, **kwargs):
    next_data = {}
    if self.services[cur_node].service_type == ServiceType.EMBEDDING:
        # turn into chat completion request
        # next_data = {"text": inputs["input"], "embedding": [item["embedding"] for item in data["data"]]}
        print("Assembing output from Embedding for next node...")
        print("Inputs to Embedding: ", inputs)
        print("Keyword arguments: ")
        for key, value in kwargs.items():
            print(f"{key}: {value}")

        next_data = {
            "input": inputs["input"],
            "messages": inputs["input"],
            "embedding": data,  # [item["embedding"] for item in data["data"]],
            "k": kwargs["k"] if "k" in kwargs else 4,
            "search_type": kwargs["search_type"] if "search_type" in kwargs else "similarity",
            "distance_threshold": kwargs["distance_threshold"] if "distance_threshold" in kwargs else None,
            "fetch_k": kwargs["fetch_k"] if "fetch_k" in kwargs else 20,
            "lambda_mult": kwargs["lambda_mult"] if "lambda_mult" in kwargs else 0.5,
            "score_threshold": kwargs["score_threshold"] if "score_threshold" in kwargs else 0.2,
            "top_n": kwargs["top_n"] if "top_n" in kwargs else 1,
        }

        print("Output from Embedding for next node:\n", next_data)

    else:
        next_data = data

    return next_data


class RetrievalToolService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        ServiceOrchestrator.align_inputs = align_inputs
        ServiceOrchestrator.align_outputs = align_outputs
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.RETRIEVALTOOL)

    def add_remote_service(self):
        embedding = MicroService(
            name="embedding",
            host=EMBEDDING_SERVICE_HOST_IP,
            port=EMBEDDING_SERVICE_PORT,
            endpoint="/v1/embeddings",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )
        retriever = MicroService(
            name="retriever",
            host=RETRIEVER_SERVICE_HOST_IP,
            port=RETRIEVER_SERVICE_PORT,
            endpoint="/v1/retrieval",
            use_remote_service=True,
            service_type=ServiceType.RETRIEVER,
        )
        rerank = MicroService(
            name="rerank",
            host=RERANK_SERVICE_HOST_IP,
            port=RERANK_SERVICE_PORT,
            endpoint="/v1/reranking",
            use_remote_service=True,
            service_type=ServiceType.RERANK,
        )

        self.megaservice.add(embedding).add(retriever).add(rerank)
        self.megaservice.flow_to(embedding, retriever)
        self.megaservice.flow_to(retriever, rerank)

    async def handle_request(self, request: Request):
        def parser_input(data, TypeClass, key):
            chat_request = None
            try:
                chat_request = TypeClass.parse_obj(data)
                query = getattr(chat_request, key)
            except:
                query = None
            return query, chat_request

        data = await request.json()
        query = None
        for key, TypeClass in zip(["text", "input", "messages"], [TextDoc, EmbeddingRequest, ChatCompletionRequest]):
            query, chat_request = parser_input(data, TypeClass, key)
            if query is not None:
                break
        if query is None:
            raise ValueError(f"Unknown request type: {data}")
        if chat_request is None:
            raise ValueError(f"Unknown request type: {data}")

        if isinstance(chat_request, ChatCompletionRequest):
            initial_inputs = {
                "messages": query,
                "input": query,  # has to be input due to embedding expects either input or text
                "search_type": chat_request.search_type if chat_request.search_type else "similarity",
                "k": chat_request.k if chat_request.k else 4,
                "distance_threshold": chat_request.distance_threshold if chat_request.distance_threshold else None,
                "fetch_k": chat_request.fetch_k if chat_request.fetch_k else 20,
                "lambda_mult": chat_request.lambda_mult if chat_request.lambda_mult else 0.5,
                "score_threshold": chat_request.score_threshold if chat_request.score_threshold else 0.2,
                "top_n": chat_request.top_n if chat_request.top_n else 1,
            }

            kwargs = {
                "search_type": chat_request.search_type if chat_request.search_type else "similarity",
                "k": chat_request.k if chat_request.k else 4,
                "distance_threshold": chat_request.distance_threshold if chat_request.distance_threshold else None,
                "fetch_k": chat_request.fetch_k if chat_request.fetch_k else 20,
                "lambda_mult": chat_request.lambda_mult if chat_request.lambda_mult else 0.5,
                "score_threshold": chat_request.score_threshold if chat_request.score_threshold else 0.2,
                "top_n": chat_request.top_n if chat_request.top_n else 1,
            }
            result_dict, runtime_graph = await self.megaservice.schedule(
                initial_inputs=initial_inputs,
                **kwargs,
            )
        else:
            result_dict, runtime_graph = await self.megaservice.schedule(initial_inputs={"input": query})

        last_node = runtime_graph.all_leaves()[-1]
        response = result_dict[last_node]
        return response

    def start(self):
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=Union[TextDoc, EmbeddingRequest, ChatCompletionRequest],
            output_datatype=Union[RerankedDoc, LLMParamsDoc],
        )
        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])
        self.service.start()

    def add_remote_service_without_rerank(self):
        embedding = MicroService(
            name="embedding",
            host=EMBEDDING_SERVICE_HOST_IP,
            port=EMBEDDING_SERVICE_PORT,
            endpoint="/v1/embeddings",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )
        retriever = MicroService(
            name="retriever",
            host=RETRIEVER_SERVICE_HOST_IP,
            port=RETRIEVER_SERVICE_PORT,
            endpoint="/v1/retrieval",
            use_remote_service=True,
            service_type=ServiceType.RETRIEVER,
        )

        self.megaservice.add(embedding).add(retriever)
        self.megaservice.flow_to(embedding, retriever)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--without-rerank", action="store_true")

    args = parser.parse_args()

    chatqna = RetrievalToolService(port=MEGA_SERVICE_PORT)
    if args.without_rerank:
        chatqna.add_remote_service_without_rerank()
    else:
        chatqna.add_remote_service()
    chatqna.start()

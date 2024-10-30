# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
from typing import Union

from comps import Gateway, MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceType
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


class RetrievalToolService(Gateway):
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()

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
            retriever_parameters = RetrieverParms(
                search_type=chat_request.search_type if chat_request.search_type else "similarity",
                k=chat_request.k if chat_request.k else 4,
                distance_threshold=chat_request.distance_threshold if chat_request.distance_threshold else None,
                fetch_k=chat_request.fetch_k if chat_request.fetch_k else 20,
                lambda_mult=chat_request.lambda_mult if chat_request.lambda_mult else 0.5,
                score_threshold=chat_request.score_threshold if chat_request.score_threshold else 0.2,
            )
            reranker_parameters = RerankerParms(
                top_n=chat_request.top_n if chat_request.top_n else 1,
            )

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

            result_dict, runtime_graph = await self.megaservice.schedule(
                initial_inputs=initial_inputs,
                retriever_parameters=retriever_parameters,
                reranker_parameters=reranker_parameters,
            )
        else:
            result_dict, runtime_graph = await self.megaservice.schedule(initial_inputs={"text": query})

        last_node = runtime_graph.all_leaves()[-1]
        response = result_dict[last_node]
        return response

    def start(self):
        super().__init__(
            megaservice=self.megaservice,
            host=self.host,
            port=self.port,
            endpoint=str(MegaServiceEndpoint.RETRIEVALTOOL),
            input_datatype=Union[TextDoc, EmbeddingRequest, ChatCompletionRequest],
            output_datatype=Union[RerankedDoc, LLMParamsDoc],
        )


if __name__ == "__main__":
    chatqna = RetrievalToolService(port=MEGA_SERVICE_PORT)
    chatqna.add_remote_service()
    chatqna.start()

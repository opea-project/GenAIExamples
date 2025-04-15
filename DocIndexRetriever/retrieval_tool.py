# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import asyncio
import os
from typing import Union

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.proto.api_protocol import ChatCompletionRequest, EmbeddingRequest
from comps.cores.proto.docarray import LLMParams, LLMParamsDoc, RerankedDoc, RerankerParms, RetrieverParms, TextDoc
from fastapi import Request

MEGA_SERVICE_PORT = os.getenv("MEGA_SERVICE_PORT", 8889)
EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)
RETRIEVER_SERVICE_HOST_IP = os.getenv("RETRIEVER_SERVICE_HOST_IP", "0.0.0.0")
RETRIEVER_SERVICE_PORT = os.getenv("RETRIEVER_SERVICE_PORT", 7000)
RERANK_SERVICE_HOST_IP = os.getenv("RERANK_SERVICE_HOST_IP", "0.0.0.0")
RERANK_SERVICE_PORT = os.getenv("RERANK_SERVICE_PORT", 8000)


def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs):
    print(f"*** Inputs to {cur_node}:\n{inputs}")
    print("--" * 50)
    for key, value in kwargs.items():
        print(f"{key}: {value}")
    if self.services[cur_node].service_type == ServiceType.EMBEDDING:
        inputs["input"] = inputs["text"]
        del inputs["text"]
    elif self.services[cur_node].service_type == ServiceType.RETRIEVER:
        # input is EmbedDoc
        """Class EmbedDoc(BaseDoc):

        text: Union[str, List[str]]
        embedding: Union[conlist(float, min_length=0), List[conlist(float, min_length=0)]]
        search_type: str = "similarity"
        k: int = 4
        distance_threshold: Optional[float] = None
        fetch_k: int = 20
        lambda_mult: float = 0.5
        score_threshold: float = 0.2
        constraints: Optional[Union[Dict[str, Any], List[Dict[str, Any]], None]] = None
        index_name: Optional[str] = None
        """
        # prepare the retriever params
        retriever_parameters = kwargs.get("retriever_parameters", None)
        if retriever_parameters:
            inputs.update(retriever_parameters.dict())
    elif self.services[cur_node].service_type == ServiceType.RERANK:
        # input is SearchedDoc
        """Class SearchedDoc(BaseDoc):

        retrieved_docs: DocList[TextDoc]
        initial_query: str
        top_n: int = 1
        """
        # prepare the reranker params
        reranker_parameters = kwargs.get("reranker_parameters", None)
        if reranker_parameters:
            inputs.update(reranker_parameters.dict())
    print(f"*** Formatted Inputs to {cur_node}:\n{inputs}")
    print("--" * 50)
    return inputs


def align_outputs(self, data, cur_node, inputs, runtime_graph, llm_parameters_dict, **kwargs):
    print(f"*** Direct Outputs from {cur_node}:\n{data}")
    print("--" * 50)

    if self.services[cur_node].service_type == ServiceType.EMBEDDING:
        # direct output from Embedding microservice is EmbeddingResponse
        """
        class EmbeddingResponse(BaseModel):
            object: str = "list"
            model: Optional[str] = None
            data: List[EmbeddingResponseData]
            usage: Optional[UsageInfo] = None

        class EmbeddingResponseData(BaseModel):
            index: int
            object: str = "embedding"
            embedding: Union[List[float], str]
        """
        # turn it into EmbedDoc
        assert isinstance(data["data"], list)
        next_data = {"text": inputs["input"], "embedding": data["data"][0]["embedding"]}  # EmbedDoc
    else:
        next_data = data

    print(f"*** Formatted Output from {cur_node} for next node:\n", next_data)
    print("--" * 50)
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
        data = await request.json()
        chat_request = ChatCompletionRequest.parse_obj(data)

        prompt = chat_request.messages

        # dummy llm params
        parameters = LLMParams(
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            chat_template=chat_request.chat_template if chat_request.chat_template else None,
            model=chat_request.model if chat_request.model else None,
        )

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
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"text": prompt},
            llm_parameters=parameters,
            retriever_parameters=retriever_parameters,
            reranker_parameters=reranker_parameters,
        )

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

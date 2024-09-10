# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import heapq
import json
import os
import re
import time
from typing import List, Optional, Union

import httpx
import msgspec
import requests
import torch
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from comps import (
    CustomLogger,
    LLMParamsDoc,
    SearchedDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    RerankingRequest,
    RerankingResponse,
    RerankingResponseData,
)


@register_microservice(
    name="opea_service@reranking_mosec",
    service_type=ServiceType.RERANK,
    endpoint="/v1/reranking",
    host="0.0.0.0",
    port=8000,
    input_datatype=SearchedDoc,
    output_datatype=LLMParamsDoc,
)
@traceable(run_type="reranking")
@register_statistics(names=["opea_service@reranking_mosec"])
def reranking(
    input: Union[SearchedDoc, RerankingRequest, ChatCompletionRequest]
) -> Union[LLMParamsDoc, RerankingResponse, ChatCompletionRequest]:
    start = time.time()
    reranking_results = []
    if input.retrieved_docs:
        docs = [doc.text for doc in input.retrieved_docs]
        url = mosec_reranking_endpoint + "/inference"
        if isinstance(input, SearchedDoc):
            query = input.initial_query
        else:
            # for RerankingRequest, ChatCompletionRequest
            query = input.input
        data = {"query": query, "docs": docs}
        resp = requests.post(url, data=msgspec.msgpack.encode(data))
        response_list = msgspec.msgpack.decode(resp.content)["scores"]
        response = torch.nn.functional.sigmoid(torch.tensor(response_list))
        length = len(response)
        resp_list = response.tolist()
        sorted_score = heapq.nlargest(length, resp_list)
        sorted_score_index = map(resp_list.index, sorted_score)

        for i in range(input.top_n):
            reranking_results.append(
                {"text": input.retrieved_docs[list(sorted_score_index)[i]].text, "score": sorted_score[i]}
            )

    statistics_dict["opea_service@reranking_mosec"].append_latency(time.time() - start, None)
    if isinstance(input, SearchedDoc):
        return LLMParamsDoc(query=input.initial_query, documents=[doc["text"] for doc in reranking_results])
    else:
        reranking_docs = []
        for doc in reranking_results:
            reranking_docs.append(RerankingResponseData(text=doc["text"], score=doc["score"]))
        if isinstance(input, RerankingRequest):
            return RerankingResponse(reranked_docs=reranking_docs)

        if isinstance(input, ChatCompletionRequest):
            input.reranked_docs = reranking_docs
            input.documents = [doc["text"] for doc in reranking_results]
            return input


if __name__ == "__main__":
    mosec_reranking_endpoint = os.getenv("MOSEC_RERANKING_ENDPOINT", "http://localhost:8080")
    print("NeuralSpeed Reranking Microservice Initialized.")
    opea_microservices["opea_service@reranking_mosec"].start()

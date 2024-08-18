# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import heapq
import json
import os
import re
import time
from typing import Union

import requests

from comps import (
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
    name="opea_service@reranking_tgi_gaudi",
    service_type=ServiceType.RERANK,
    endpoint="/v1/reranking",
    host="0.0.0.0",
    port=8000,
    input_datatype=SearchedDoc,
    output_datatype=LLMParamsDoc,
)
@register_statistics(names=["opea_service@reranking_tgi_gaudi"])
def reranking(
    input: Union[SearchedDoc, RerankingRequest, ChatCompletionRequest]
) -> Union[LLMParamsDoc, RerankingResponse, ChatCompletionRequest]:

    start = time.time()
    reranking_results = []
    if input.retrieved_docs:
        docs = [doc.text for doc in input.retrieved_docs]
        url = tei_reranking_endpoint + "/rerank"
        if isinstance(input, SearchedDoc):
            query = input.initial_query
        else:
            # for RerankingRequest, ChatCompletionRequest
            query = input.input
        data = {"query": query, "texts": docs}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        response_data = response.json()

        for best_response in response_data[: input.top_n]:
            reranking_results.append(
                {"text": input.retrieved_docs[best_response["index"]].text, "score": best_response["score"]}
            )

    statistics_dict["opea_service@reranking_tgi_gaudi"].append_latency(time.time() - start, None)
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
    tei_reranking_endpoint = os.getenv("TEI_RERANKING_ENDPOINT", "http://localhost:8080")
    opea_microservices["opea_service@reranking_tgi_gaudi"].start()

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import time
from typing import Union

import aiohttp

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
from comps.cores.mega.utils import get_access_token
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    RerankingRequest,
    RerankingResponse,
    RerankingResponseData,
)

logger = CustomLogger("reranking_tei")
logflag = os.getenv("LOGFLAG", False)

# Environment variables
TOKEN_URL = os.getenv("TOKEN_URL")
CLIENTID = os.getenv("CLIENTID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


@register_microservice(
    name="opea_service@reranking_tei",
    service_type=ServiceType.RERANK,
    endpoint="/v1/reranking",
    host="0.0.0.0",
    port=8000,
    input_datatype=Union[SearchedDoc, RerankingRequest, ChatCompletionRequest],
    output_datatype=Union[LLMParamsDoc, RerankingResponse, ChatCompletionRequest],
)
@register_statistics(names=["opea_service@reranking_tei"])
async def reranking(
    input: Union[SearchedDoc, RerankingRequest, ChatCompletionRequest]
) -> Union[LLMParamsDoc, RerankingResponse, ChatCompletionRequest]:
    if logflag:
        logger.info(input)
    start = time.time()
    reranking_results = []
    access_token = (
        get_access_token(TOKEN_URL, CLIENTID, CLIENT_SECRET) if TOKEN_URL and CLIENTID and CLIENT_SECRET else None
    )
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
        if access_token:
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=json.dumps(data), headers=headers) as response:
                response_data = await response.json()

        for best_response in response_data[: input.top_n]:
            reranking_results.append(
                {"text": input.retrieved_docs[best_response["index"]].text, "score": best_response["score"]}
            )

    statistics_dict["opea_service@reranking_tei"].append_latency(time.time() - start, None)
    if isinstance(input, SearchedDoc):
        result = [doc["text"] for doc in reranking_results]
        if logflag:
            logger.info(result)
        return LLMParamsDoc(query=input.initial_query, documents=result)
    else:
        reranking_docs = []
        for doc in reranking_results:
            reranking_docs.append(RerankingResponseData(text=doc["text"], score=doc["score"]))
        if isinstance(input, RerankingRequest):
            result = RerankingResponse(reranked_docs=reranking_docs)
            if logflag:
                logger.info(result)
            return result

        if isinstance(input, ChatCompletionRequest):
            input.reranked_docs = reranking_docs
            input.documents = [doc["text"] for doc in reranking_results]
            if logflag:
                logger.info(input)
            return input


if __name__ == "__main__":
    tei_reranking_endpoint = os.getenv("TEI_RERANKING_ENDPOINT", "http://localhost:8080")
    opea_microservices["opea_service@reranking_tei"].start()

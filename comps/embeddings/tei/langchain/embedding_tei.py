# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import time
from typing import List, Union

from huggingface_hub import AsyncInferenceClient

from comps import (
    CustomLogger,
    EmbedDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)
from comps.cores.mega.utils import get_access_token
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingResponseData,
)

logger = CustomLogger("embedding_tei_langchain")
logflag = os.getenv("LOGFLAG", False)

# Environment variables
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
TOKEN_URL = os.getenv("TOKEN_URL")
CLIENTID = os.getenv("CLIENTID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TEI_EMBEDDING_ENDPOINT = os.getenv("TEI_EMBEDDING_ENDPOINT", "http://localhost:8080")


@register_microservice(
    name="opea_service@embedding_tei_langchain",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=6000,
)
@register_statistics(names=["opea_service@embedding_tei_langchain"])
async def embedding(
    input: Union[TextDoc, EmbeddingRequest, ChatCompletionRequest]
) -> Union[EmbedDoc, EmbeddingResponse, ChatCompletionRequest]:
    start = time.time()
    access_token = (
        get_access_token(TOKEN_URL, CLIENTID, CLIENT_SECRET) if TOKEN_URL and CLIENTID and CLIENT_SECRET else None
    )
    async_client = get_async_inference_client(access_token)
    if logflag:
        logger.info(input)
    if isinstance(input, TextDoc):
        embed_vector = await aembed_query(input.text, async_client)
        embedding_res = embed_vector[0] if isinstance(input.text, str) else embed_vector
        res = EmbedDoc(text=input.text, embedding=embedding_res)
    else:
        embed_vector = await aembed_query(input.input, async_client)
        if input.dimensions is not None:
            embed_vector = [embed_vector[i][: input.dimensions] for i in range(len(embed_vector))]

        # for standard openai embedding format
        res = EmbeddingResponse(
            data=[EmbeddingResponseData(index=i, embedding=embed_vector[i]) for i in range(len(embed_vector))]
        )

        if isinstance(input, ChatCompletionRequest):
            input.embedding = res
            # keep
            res = input

    statistics_dict["opea_service@embedding_tei_langchain"].append_latency(time.time() - start, None)
    if logflag:
        logger.info(res)
    return res


async def aembed_query(
    text: Union[str, List[str]], async_client: AsyncInferenceClient, model_kwargs=None, task=None
) -> List[List[float]]:
    texts = [text] if isinstance(text, str) else text
    response = await aembed_documents(texts, async_client, model_kwargs=model_kwargs, task=task)
    return response


async def aembed_documents(
    texts: List[str], async_client: AsyncInferenceClient, model_kwargs=None, task=None
) -> List[List[float]]:
    texts = [text.replace("\n", " ") for text in texts]
    _model_kwargs = model_kwargs or {}
    responses = await async_client.post(json={"inputs": texts, **_model_kwargs}, task=task)
    return json.loads(responses.decode())


def get_async_inference_client(access_token: str) -> AsyncInferenceClient:
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    return AsyncInferenceClient(model=TEI_EMBEDDING_ENDPOINT, token=HUGGINGFACEHUB_API_TOKEN, headers=headers)


if __name__ == "__main__":
    logger.info("TEI Gaudi Embedding initialized.")
    opea_microservices["opea_service@embedding_tei_langchain"].start()

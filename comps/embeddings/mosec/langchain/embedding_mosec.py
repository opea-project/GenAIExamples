# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
import time
from typing import List, Optional, Union

from langchain_community.embeddings import OpenAIEmbeddings

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
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingResponseData,
)

logger = CustomLogger("embedding_mosec")
logflag = os.getenv("LOGFLAG", False)


class MosecEmbeddings(OpenAIEmbeddings):
    async def _aget_len_safe_embeddings(
        self, texts: List[str], *, engine: str, chunk_size: Optional[int] = None
    ) -> List[List[float]]:
        _chunk_size = chunk_size or self.chunk_size
        batched_embeddings: List[List[float]] = []
        response = self.client.create(input=texts, **self._invocation_params)
        if not isinstance(response, dict):
            response = response.model_dump()
        batched_embeddings.extend(r["embedding"] for r in response["data"])

        _cached_empty_embedding: Optional[List[float]] = None

        async def empty_embedding() -> List[float]:
            nonlocal _cached_empty_embedding
            if _cached_empty_embedding is None:
                average_embedded = self.client.create(input="", **self._invocation_params)
                if not isinstance(average_embedded, dict):
                    average_embedded = average_embedded.model_dump()
                _cached_empty_embedding = average_embedded["data"][0]["embedding"]
            return _cached_empty_embedding

        async def get_embedding(e: Optional[List[float]]) -> List[float]:
            return e if e is not None else await empty_embedding()

        embeddings = await asyncio.gather(*[get_embedding(e) for e in batched_embeddings])
        return embeddings


@register_microservice(
    name="opea_service@embedding_mosec",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=6000,
    input_datatype=TextDoc,
    output_datatype=EmbedDoc,
)
@register_statistics(names=["opea_service@embedding_mosec"])
async def embedding(
    input: Union[TextDoc, EmbeddingRequest, ChatCompletionRequest]
) -> Union[EmbedDoc, EmbeddingResponse, ChatCompletionRequest]:
    if logflag:
        logger.info(input)
    start = time.time()
    if isinstance(input, TextDoc):
        embed_vector = await get_embeddings(input.text)
        embedding_res = embed_vector[0] if isinstance(input.text, str) else embed_vector
        res = EmbedDoc(text=input.text, embedding=embedding_res)
    else:
        embed_vector = await get_embeddings(input.input)
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

    statistics_dict["opea_service@embedding_mosec"].append_latency(time.time() - start, None)
    if logflag:
        logger.info(res)
    return res


async def get_embeddings(text: Union[str, List[str]]) -> List[List[float]]:
    texts = [text] if isinstance(text, str) else text
    embed_vector = await embeddings.aembed_documents(texts)
    return embed_vector


if __name__ == "__main__":
    MOSEC_EMBEDDING_ENDPOINT = os.environ.get("MOSEC_EMBEDDING_ENDPOINT", "http://127.0.0.1:8080")
    os.environ["OPENAI_API_BASE"] = MOSEC_EMBEDDING_ENDPOINT
    os.environ["OPENAI_API_KEY"] = "Dummy key"
    MODEL_ID = "/home/user/bge-large-zh-v1.5"
    embeddings = MosecEmbeddings(model=MODEL_ID)
    logger.info("Mosec Embedding initialized.")
    opea_microservices["opea_service@embedding_mosec"].start()

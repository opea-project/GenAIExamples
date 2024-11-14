# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import List, Union

from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference

from comps import CustomLogger, EmbedDoc, ServiceType, TextDoc, opea_microservices, register_microservice
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingResponseData,
)

logger = CustomLogger("embedding_tei_llamaindex")
logflag = os.getenv("LOGFLAG", False)


@register_microservice(
    name="opea_service@embedding_tei_llamaindex",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=6000,
    input_datatype=TextDoc,
    output_datatype=EmbedDoc,
)
async def embedding(
    input: Union[TextDoc, EmbeddingRequest, ChatCompletionRequest]
) -> Union[EmbedDoc, EmbeddingResponse, ChatCompletionRequest]:
    if logflag:
        logger.info(input)
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

    if logflag:
        logger.info(res)
    return res


async def get_embeddings(text: Union[str, List[str]]) -> List[List[float]]:
    texts = [text] if isinstance(text, str) else text
    embed_vector = await embeddings._aget_text_embeddings(texts)
    return embed_vector


if __name__ == "__main__":
    tei_embedding_model_name = os.getenv("TEI_EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")
    tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT", "http://localhost:8090")
    embeddings = TextEmbeddingsInference(model_name=tei_embedding_model_name, base_url=tei_embedding_endpoint)
    logger.info("TEI Gaudi Embedding initialized.")
    opea_microservices["opea_service@embedding_tei_llamaindex"].start()

# Copyright (C) 2024 Prediction Guard, Inc.
# SPDX-License-Identified: Apache-2.0


import os
import time
from typing import List, Optional, Union

from predictionguard import PredictionGuard

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

logger = CustomLogger("embedding_predictionguard")
logflag = os.getenv("LOGFLAG", False)

# Initialize Prediction Guard client
client = PredictionGuard()


@register_microservice(
    name="opea_service@embedding_predictionguard",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=6000,
    input_datatype=TextDoc,
    output_datatype=EmbedDoc,
)
@register_statistics(names=["opea_service@embedding_predictionguard"])
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
        input.dimensions = input.dimensions if input.dimensions is not None else 512
        embed_vector = [embed_vector[i][: input.dimensions] for i in range(len(embed_vector))]

        # for standard openai embedding format
        res = EmbeddingResponse(
            data=[EmbeddingResponseData(index=i, embedding=embed_vector[i]) for i in range(len(embed_vector))]
        )

        if isinstance(input, ChatCompletionRequest):
            input.embedding = res
            # keep
            res = input

    statistics_dict["opea_service@embedding_predictionguard"].append_latency(time.time() - start, None)
    if logflag:
        logger.info(res)
    return res


async def get_embeddings(text: Union[str, List[str]]) -> List[List[float]]:
    texts = [text] if isinstance(text, str) else text
    texts = [{"text": texts[i]} for i in range(len(texts))]
    response = client.embeddings.create(model=pg_embedding_model_name, input=texts)["data"]
    embed_vector = [response[i]["embedding"] for i in range(len(response))]
    return embed_vector


if __name__ == "__main__":
    pg_embedding_model_name = os.getenv("PG_EMBEDDING_MODEL_NAME", "bridgetower-large-itm-mlm-itc")
    print("Prediction Guard Embedding initialized.")
    opea_microservices["opea_service@embedding_predictionguard"].start()

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from typing import List, Optional

from langchain_community.embeddings import OpenAIEmbeddings

from comps import (
    EmbedDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)


class MosecEmbeddings(OpenAIEmbeddings):
    def _get_len_safe_embeddings(
        self, texts: List[str], *, engine: str, chunk_size: Optional[int] = None
    ) -> List[List[float]]:
        _chunk_size = chunk_size or self.chunk_size
        batched_embeddings: List[List[float]] = []
        response = self.client.create(input=texts, **self._invocation_params)
        if not isinstance(response, dict):
            response = response.model_dump()
        batched_embeddings.extend(r["embedding"] for r in response["data"])

        _cached_empty_embedding: Optional[List[float]] = None

        def empty_embedding() -> List[float]:
            nonlocal _cached_empty_embedding
            if _cached_empty_embedding is None:
                average_embedded = self.client.create(input="", **self._invocation_params)
                if not isinstance(average_embedded, dict):
                    average_embedded = average_embedded.model_dump()
                _cached_empty_embedding = average_embedded["data"][0]["embedding"]
            return _cached_empty_embedding

        return [e if e is not None else empty_embedding() for e in batched_embeddings]


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
def embedding(input: TextDoc) -> EmbedDoc:
    start = time.time()
    embed_vector = embeddings.embed_query(input.text)
    res = EmbedDoc(text=input.text, embedding=embed_vector)
    statistics_dict["opea_service@embedding_mosec"].append_latency(time.time() - start, None)
    return res


if __name__ == "__main__":
    MOSEC_EMBEDDING_ENDPOINT = os.environ.get("MOSEC_EMBEDDING_ENDPOINT", "http://127.0.0.1:8080")
    os.environ["OPENAI_API_BASE"] = MOSEC_EMBEDDING_ENDPOINT
    os.environ["OPENAI_API_KEY"] = "Dummy key"
    MODEL_ID = "/home/user/bge-large-zh-v1.5"
    embeddings = MosecEmbeddings(model=MODEL_ID)
    print("Mosec Embedding initialized.")
    opea_microservices["opea_service@embedding_mosec"].start()

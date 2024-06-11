# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from langchain_community.embeddings import HuggingFaceHubEmbeddings
from langsmith import traceable

from comps import (
    EmbedDoc768,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)


@register_microservice(
    name="opea_service@embedding_tgi_gaudi",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=6000,
    input_datatype=TextDoc,
    output_datatype=EmbedDoc768,
)
@traceable(run_type="embedding")
@register_statistics(names=["opea_service@embedding_tgi_gaudi"])
def embedding(input: TextDoc) -> EmbedDoc768:
    start = time.time()
    embed_vector = embeddings.embed_query(input.text)
    embed_vector = embed_vector[:768]  # Keep only the first 768 elements
    res = EmbedDoc768(text=input.text, embedding=embed_vector)
    statistics_dict["opea_service@embedding_tgi_gaudi"].append_latency(time.time() - start, None)
    return res


if __name__ == "__main__":
    tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT", "http://localhost:8080")
    embeddings = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    print("TEI Gaudi Embedding initialized.")
    opea_microservices["opea_service@embedding_tgi_gaudi"].start()

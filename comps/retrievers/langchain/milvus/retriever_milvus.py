# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import time

from config import COLLECTION_NAME, EMBED_ENDPOINT, EMBED_MODEL, MILVUS_HOST, MILVUS_PORT
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_milvus.vectorstores import Milvus
from langsmith import traceable

from comps import (
    EmbedDoc768,
    SearchedDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)


@register_microservice(
    name="opea_service@retriever_milvus",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/retrieval",
    host="0.0.0.0",
    port=7000,
)
@traceable(run_type="retriever")
@register_statistics(names=["opea_service@retriever_milvus"])
def retrieve(input: EmbedDoc768) -> SearchedDoc:
    vector_db = Milvus(
        embeddings,
        connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT},
        collection_name=COLLECTION_NAME,
    )
    start = time.time()
    search_res = vector_db.similarity_search_by_vector(embedding=input.embedding)
    searched_docs = []
    for r in search_res:
        searched_docs.append(TextDoc(text=r.page_content))
    result = SearchedDoc(retrieved_docs=searched_docs, initial_query=input.text)
    statistics_dict["opea_service@retriever_milvus"].append_latency(time.time() - start, None)
    return result


if __name__ == "__main__":
    # Create vectorstore
    if EMBED_ENDPOINT:
        # create embeddings using TEI endpoint service
        embeddings = HuggingFaceHubEmbeddings(model=EMBED_ENDPOINT)
    else:
        # create embeddings using local embedding model
        embeddings = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    opea_microservices["opea_service@retriever_milvus"].start()

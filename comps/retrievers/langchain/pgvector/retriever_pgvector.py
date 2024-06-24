# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from config import EMBED_MODEL, INDEX_NAME, PG_CONNECTION_STRING, PORT
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores import PGVector
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

tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT")


@register_microservice(
    name="opea_service@retriever_pgvector",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/retrieval",
    host="0.0.0.0",
    port=PORT,
)
@traceable(run_type="retriever")
@register_statistics(names=["opea_service@retriever_pgvector"])
def retrieve(input: EmbedDoc768) -> SearchedDoc:
    start = time.time()
    search_res = vector_db.similarity_search_by_vector(embedding=input.embedding)
    searched_docs = []
    for r in search_res:
        searched_docs.append(TextDoc(text=r.page_content))
    result = SearchedDoc(retrieved_docs=searched_docs, initial_query=input.text)
    statistics_dict["opea_service@retriever_pgvector"].append_latency(time.time() - start, None)
    return result


if __name__ == "__main__":
    # Create vectorstore
    if tei_embedding_endpoint:
        # create embeddings using TEI endpoint service
        embeddings = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    else:
        # create embeddings using local embedding model
        embeddings = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    vector_db = PGVector(
        embedding_function=embeddings,
        collection_name=INDEX_NAME,
        connection_string=PG_CONNECTION_STRING,
    )
    opea_microservices["opea_service@retriever_pgvector"].start()

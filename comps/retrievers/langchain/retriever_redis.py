# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores import Redis
from langsmith import traceable
from redis_config import EMBED_MODEL, INDEX_NAME, INDEX_SCHEMA, REDIS_URL

from comps import EmbedDoc768, SearchedDoc, ServiceType, TextDoc, opea_microservices, register_microservice

tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT")


@register_microservice(
    name="opea_service@retriever_redis",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/retrieval",
    host="0.0.0.0",
    port=7000,
)
@traceable(run_type="retriever")
def retrieve(input: EmbedDoc768) -> SearchedDoc:
    # Create vectorstore
    if tei_embedding_endpoint:
        # create embeddings using TEI endpoint service
        embeddings = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    else:
        # create embeddings using local embedding model
        embeddings = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    vector_db = Redis.from_existing_index(
        embedding=embeddings,
        index_name=INDEX_NAME,
        redis_url=REDIS_URL,
        schema=INDEX_SCHEMA,
    )
    search_res = vector_db.similarity_search_by_vector(embedding=input.embedding)
    searched_docs = []
    for r in search_res:
        searched_docs.append(TextDoc(text=r.page_content))
    result = SearchedDoc(retrieved_docs=searched_docs, initial_query=input.text)
    return result


if __name__ == "__main__":
    opea_microservices["opea_service@retriever_redis"].start()

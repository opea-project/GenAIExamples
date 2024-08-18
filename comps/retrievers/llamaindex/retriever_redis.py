# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from llama_index.core.vector_stores.types import VectorStoreQuery
from llama_index.vector_stores.redis import RedisVectorStore
from redis_config import INDEX_NAME, REDIS_URL

from comps import EmbedDoc, SearchedDoc, ServiceType, TextDoc, opea_microservices, register_microservice

tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT")


@register_microservice(
    name="opea_service@retriever_redis",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/retrieval",
    host="0.0.0.0",
    port=7000,
)
def retrieve(input: EmbedDoc) -> SearchedDoc:
    vector_store_query = VectorStoreQuery(query_embedding=input.embedding)
    search_res = vector_store.query(query=vector_store_query)
    searched_docs = []
    for node, id, similarity in zip(search_res.nodes, search_res.ids, search_res.similarities):
        searched_docs.append(TextDoc(text=node.get_content()))
    result = SearchedDoc(retrieved_docs=searched_docs, initial_query=input.text)
    return result


if __name__ == "__main__":

    vector_store = RedisVectorStore(
        redis_url=REDIS_URL,
    )
    opea_microservices["opea_service@retriever_redis"].start()

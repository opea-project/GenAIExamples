# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from langsmith import traceable
from llama_index.core.vector_stores.types import VectorStoreQuery
from llama_index.vector_stores.redis import RedisVectorStore
from redis_config import INDEX_NAME, REDIS_URL
from redisvl.schema import IndexSchema

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
    vector_store_query = VectorStoreQuery(query_embedding=input.embedding)
    search_res = vector_store.query(query=vector_store_query)
    searched_docs = []
    for node, id, similarity in zip(search_res.nodes, search_res.ids, search_res.similarities):
        searched_docs.append(TextDoc(text=node.get_content()))
    result = SearchedDoc(retrieved_docs=searched_docs, initial_query=input.text)
    return result


if __name__ == "__main__":
    custom_schema = IndexSchema.from_dict(
        {
            "index": {"name": INDEX_NAME, "prefix": "doc"},
            "fields": [
                {"name": "id", "type": "tag"},
                {"name": "doc_id", "type": "tag"},
                {"name": "text", "type": "text"},
                {"name": "content", "type": "text"},
                {"name": "source", "type": "text"},
                {"name": "start_index", "type": "numeric"},
                {
                    "name": "vector",
                    "type": "vector",
                    "attrs": {"dims": 768, "algorithm": "HNSW", "date_type": "FLOAT32"},
                },
            ],
        }
    )

    vector_store = RedisVectorStore(
        schema=custom_schema,
        redis_url=REDIS_URL,
    )
    opea_microservices["opea_service@retriever_redis"].start()

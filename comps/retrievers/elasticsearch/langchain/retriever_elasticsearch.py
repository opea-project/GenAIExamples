# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
from typing import Union

from config import EMBED_MODEL, ES_CONNECTION_STRING, INDEX_NAME, LOG_FLAG, TEI_ENDPOINT
from elasticsearch import Elasticsearch
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings

from comps import (
    CustomLogger,
    EmbedDoc,
    SearchedDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger(__name__)


def create_index() -> None:
    if not es_client.indices.exists(index=INDEX_NAME):
        es_client.indices.create(index=INDEX_NAME)


def get_embedder() -> Union[HuggingFaceEndpointEmbeddings, HuggingFaceBgeEmbeddings]:
    """Obtain required Embedder."""

    if TEI_ENDPOINT:
        return HuggingFaceEndpointEmbeddings(model=TEI_ENDPOINT)
    else:
        return HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)


def get_elastic_store(embedder: Union[HuggingFaceEndpointEmbeddings, HuggingFaceBgeEmbeddings]) -> ElasticsearchStore:
    """Get Elasticsearch vector store."""

    return ElasticsearchStore(index_name=INDEX_NAME, embedding=embedder, es_connection=es_client)


@register_microservice(
    name="opea_service@retriever_elasticsearch",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/retrieval",
    host="0.0.0.0",
    port=7000,
)
@register_statistics(names=["opea_service@retriever_elasticsearch"])
async def retrieve(input: EmbedDoc) -> SearchedDoc:
    """Retrieve documents based on similarity search type."""
    if LOG_FLAG:
        logger.info(input)
    start = time.time()

    if input.search_type == "similarity":
        docs_and_similarities = vector_db.similarity_search_by_vector_with_relevance_scores(
            embedding=input.embedding, k=input.k
        )
        search_res = [doc for doc, _ in docs_and_similarities]

    elif input.search_type == "similarity_distance_threshold":
        if input.distance_threshold is None:
            raise ValueError("distance_threshold must be provided for " + "similarity_distance_threshold retriever")
        docs_and_similarities = vector_db.similarity_search_by_vector_with_relevance_scores(
            embedding=input.embedding, k=input.k
        )
        search_res = [doc for doc, similarity in docs_and_similarities if similarity > input.distance_threshold]

    elif input.search_type == "similarity_score_threshold":
        docs_and_similarities = vector_db.similarity_search_by_vector_with_relevance_scores(query=input.text, k=input.k)
        search_res = [doc for doc, similarity in docs_and_similarities if similarity > input.score_threshold]

    elif input.search_type == "mmr":
        search_res = vector_db.max_marginal_relevance_search(
            query=input.text, k=input.k, fetch_k=input.fetch_k, lambda_mult=input.lambda_mult
        )

    else:
        raise ValueError(f"{input.search_type} not valid")

    searched_docs = []
    for r in search_res:
        searched_docs.append(TextDoc(text=r.page_content))
    result = SearchedDoc(retrieved_docs=searched_docs, initial_query=input.text)

    statistics_dict["opea_service@retriever_elasticsearch"].append_latency(time.time() - start, None)

    if LOG_FLAG:
        logger.info(result)

    return result


if __name__ == "__main__":
    es_client = Elasticsearch(hosts=ES_CONNECTION_STRING)
    vector_db = get_elastic_store(get_embedder())
    create_index()
    opea_microservices["opea_service@retriever_elasticsearch"].start()

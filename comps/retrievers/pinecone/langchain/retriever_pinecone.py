# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from config import EMBED_MODEL, PINECONE_API_KEY, PINECONE_INDEX_NAME
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

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

logger = CustomLogger("retriever_pinecone")
logflag = os.getenv("LOGFLAG", False)

tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT")


@register_microservice(
    name="opea_service@retriever_pinecone",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/retrieval",
    host="0.0.0.0",
    port=7000,
)
@register_statistics(names=["opea_service@retriever_pinecone"])
def retrieve(input: EmbedDoc) -> SearchedDoc:
    if logflag:
        logger.info(input)
    start = time.time()

    pc = Pinecone(api_key=PINECONE_API_KEY)

    index = pc.Index(PINECONE_INDEX_NAME)
    if logflag:
        logger.info(index.describe_index_stats()["total_vector_count"])
    # check if the Pinecone index has data
    if index.describe_index_stats()["total_vector_count"] == 0:
        result = SearchedDoc(retrieved_docs=[], initial_query=input.text)
        statistics_dict["opea_service@retriever_pinecone"].append_latency(time.time() - start, None)
        if logflag:
            logger.info(result)
        return result

    search_res = vector_db.max_marginal_relevance_search(query=input.text, k=input.k, fetch_k=input.fetch_k)
    # if the Pinecone index has data, perform the search
    if input.search_type == "similarity":
        docs_and_similarities = vector_db.similarity_search_by_vector_with_score(embedding=input.embedding, k=input.k)
        search_res = [doc for doc, _ in docs_and_similarities]
    elif input.search_type == "similarity_distance_threshold":
        if input.distance_threshold is None:
            raise ValueError("distance_threshold must be provided for " + "similarity_distance_threshold retriever")
        docs_and_similarities = vector_db.similarity_search_by_vector_with_score(embedding=input.embedding, k=input.k)
        search_res = [doc for doc, similarity in docs_and_similarities if similarity > input.distance_threshold]
    elif input.search_type == "similarity_score_threshold":
        docs_and_similarities = vector_db.similarity_search_by_vector_with_score(query=input.text, k=input.k)
        search_res = [doc for doc, similarity in docs_and_similarities if similarity > input.score_threshold]
    elif input.search_type == "mmr":
        search_res = vector_db.max_marginal_relevance_search(
            query=input.text, k=input.k, fetch_k=input.fetch_k, lambda_mult=input.lambda_mult
        )
    searched_docs = []
    for r in search_res:
        searched_docs.append(TextDoc(text=r.page_content))
    result = SearchedDoc(retrieved_docs=searched_docs, initial_query=input.text)
    statistics_dict["opea_service@retriever_pinecone"].append_latency(time.time() - start, None)
    if logflag:
        logger.info(result)
    return result


if __name__ == "__main__":
    # Create vectorstore
    if tei_embedding_endpoint:
        # create embeddings using TEI endpoint service
        embeddings = HuggingFaceEndpointEmbeddings(model=tei_embedding_endpoint)
    else:
        # create embeddings using local embedding model
        embeddings = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    pc = Pinecone(api_key=PINECONE_API_KEY)
    spec = ServerlessSpec(cloud="aws", region="us-east-1")

    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

    # For testing purposes we want to create a fresh index each time.
    # In production you would probably keep your index and
    # replace this with a check if the index doesn't exist then create it.
    if PINECONE_INDEX_NAME in existing_indexes:
        pc.configure_index(PINECONE_INDEX_NAME, deletion_protection="disabled")
        pc.delete_index(PINECONE_INDEX_NAME)
        time.sleep(1)

    pc.create_index(
        PINECONE_INDEX_NAME,
        dimension=1024,  # Based on TEI Embedding service using BAAI/bge-large-en-v1.5
        deletion_protection="disabled",
        spec=spec,
    )
    while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        time.sleep(1)

    index = pc.Index(PINECONE_INDEX_NAME)
    vector_db = PineconeVectorStore(index=index, embedding=embeddings)

    opea_microservices["opea_service@retriever_pinecone"].start()

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import time
from typing import Union

from config import EMBED_ENDPOINT, EMBED_MODEL, NEO4J_PASSWORD, NEO4J_URL, NEO4J_USERNAME
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores import Neo4jVector

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
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResponseData,
)

logger = CustomLogger("retriever_neo4j")
logflag = os.getenv("LOGFLAG", False)


@register_microservice(
    name="opea_service@retriever_neo4j",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/retrieval",
    host="0.0.0.0",
    port=7000,
)
@register_statistics(names=["opea_service@retriever_neo4j"])
def retrieve(
    input: Union[EmbedDoc, RetrievalRequest, ChatCompletionRequest]
) -> Union[SearchedDoc, RetrievalResponse, ChatCompletionRequest]:
    if logflag:
        logger.info(input)
    start = time.time()

    if isinstance(input, EmbedDoc):
        query = input.text
    else:
        # for RetrievalRequest, ChatCompletionRequest
        query = input.input

    if input.search_type == "similarity":
        search_res = vector_db.similarity_search_by_vector(embedding=input.embedding, query=input.text, k=input.k)
    elif input.search_type == "similarity_distance_threshold":
        if input.distance_threshold is None:
            raise ValueError("distance_threshold must be provided for " + "similarity_distance_threshold retriever")
        search_res = vector_db.similarity_search_by_vector(
            embedding=input.embedding, query=input.text, k=input.k, distance_threshold=input.distance_threshold
        )
    elif input.search_type == "similarity_score_threshold":
        docs_and_similarities = vector_db.similarity_search_with_relevance_scores(
            query=input.text, k=input.k, score_threshold=input.score_threshold
        )
        search_res = [doc for doc, _ in docs_and_similarities]
    elif input.search_type == "mmr":
        search_res = vector_db.max_marginal_relevance_search(
            query=input.text, k=input.k, fetch_k=input.fetch_k, lambda_mult=input.lambda_mult
        )
    else:
        raise ValueError(f"{input.search_type} not valid")

    # return different response format
    retrieved_docs = []
    if isinstance(input, EmbedDoc):
        for r in search_res:
            retrieved_docs.append(TextDoc(text=r.page_content))
        result = SearchedDoc(retrieved_docs=retrieved_docs, initial_query=input.text)
    else:
        for r in search_res:
            retrieved_docs.append(RetrievalResponseData(text=r.page_content, metadata=r.metadata))
        if isinstance(input, RetrievalRequest):
            result = RetrievalResponse(retrieved_docs=retrieved_docs)
        elif isinstance(input, ChatCompletionRequest):
            input.retrieved_docs = retrieved_docs
            input.documents = [doc.text for doc in retrieved_docs]
            result = input

    statistics_dict["opea_service@retriever_neo4j"].append_latency(time.time() - start, None)
    if logflag:
        logger.info(result)
    return result


if __name__ == "__main__":

    if EMBED_ENDPOINT:
        # create embeddings using TEI endpoint service
        hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        embeddings = HuggingFaceHubEmbeddings(model=EMBED_ENDPOINT, huggingfacehub_api_token=hf_token)
    else:
        # create embeddings using local embedding model
        embeddings = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    vector_db = Neo4jVector.from_existing_graph(
        embedding=embeddings,
        url=NEO4J_URL,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        node_label="__Entity__",
        text_node_properties=["id", "description"],
        embedding_node_property="embedding",
    )
    opea_microservices["opea_service@retriever_neo4j"].start()

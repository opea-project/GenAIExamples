# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from typing import Callable, List, Union

import numpy as np
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from opensearch_config import EMBED_MODEL, INDEX_NAME, OPENSEARCH_INITIAL_ADMIN_PASSWORD, OPENSEARCH_URL
from pydantic import conlist

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

logger = CustomLogger("retriever_opensearch")
logflag = os.getenv("LOGFLAG", False)

tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT", None)


async def search_all_embeddings_vectors(
    embeddings: Union[conlist(float, min_length=0), List[conlist(float, min_length=0)]], func: Callable, *args, **kwargs
):
    try:
        if not isinstance(embeddings, np.ndarray):
            embeddings = np.array(embeddings)

        if not np.issubdtype(embeddings.dtype, np.floating):
            raise ValueError("All embeddings values must be floating point numbers")

        if embeddings.ndim == 1:
            return await func(embedding=embeddings, *args, **kwargs)
        elif embeddings.ndim == 2:
            responses = []
            for emb in embeddings:
                response = await func(embedding=emb, *args, **kwargs)
                responses.extend(response)
            return responses
        else:
            raise ValueError("Embeddings must be one or two dimensional")
    except Exception as e:
        raise ValueError(f"Embedding data is not valid: {e}")


@register_microservice(
    name="opea_service@retriever_opensearch",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/retrieval",
    host="0.0.0.0",
    port=7000,
)
@register_statistics(names=["opea_service@retriever_opensearch"])
async def retrieve(
    input: Union[EmbedDoc, RetrievalRequest, ChatCompletionRequest]
) -> Union[SearchedDoc, RetrievalResponse, ChatCompletionRequest]:
    if logflag:
        logger.info(input)
    start = time.time()

    # Check if the index exists and has documents
    doc_count = 0

    index_exists = vector_db.client.indices.exists(index=INDEX_NAME)
    if index_exists:
        doc_count = vector_db.client.count(index=INDEX_NAME)["count"]
    if (not index_exists) or doc_count == 0:
        search_res = []
    else:
        if isinstance(input, EmbedDoc):
            query = input.text
        else:
            # for RetrievalRequest, ChatCompletionRequest
            query = input.input
        # if the OpenSearch index has data, perform the search
        if input.search_type == "similarity":
            search_res = await search_all_embeddings_vectors(
                embeddings=input.embedding,
                func=vector_db.asimilarity_search_by_vector,
                k=input.k,
            )
        elif input.search_type == "similarity_distance_threshold":
            if input.distance_threshold is None:
                raise ValueError("distance_threshold must be provided for " + "similarity_distance_threshold retriever")
            search_res = await search_all_embeddings_vectors(
                embeddings=input.embedding,
                func=vector_db.asimilarity_search_by_vector,
                k=input.k,
                distance_threshold=input.distance_threshold,
            )
        elif input.search_type == "similarity_score_threshold":
            doc_and_similarities = await vector_db.asimilarity_search_with_relevance_scores(
                query=input.text, k=input.k, score_threshold=input.score_threshold
            )
            search_res = [doc for doc, _ in doc_and_similarities]
        elif input.search_type == "mmr":
            search_res = await vector_db.amax_marginal_relevance_search(
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

    statistics_dict["opea_service@retriever_opensearch"].append_latency(time.time() - start, None)
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

    auth = ("admin", OPENSEARCH_INITIAL_ADMIN_PASSWORD)
    vector_db = OpenSearchVectorSearch(
        opensearch_url=OPENSEARCH_URL,
        index_name=INDEX_NAME,
        embedding_function=embeddings,
        http_auth=auth,
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
    )
    opea_microservices["opea_service@retriever_opensearch"].start()

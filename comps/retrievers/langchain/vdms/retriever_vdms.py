# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores.vdms import VDMS, VDMS_Client
from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings
from vdms_config import DEBUG, DISTANCE_STRATEGY, EMBED_MODEL, INDEX_NAME, SEARCH_ENGINE, VDMS_HOST, VDMS_PORT

from comps import (
    EmbedDoc,
    SearchedDoc,
    SearchedMultimodalDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT")
hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
use_clip = int(os.getenv("USECLIP"))

if use_clip:
    import sys

    sys.path.append("../../../embeddings/langchain_multimodal/")
    from embeddings_clip import vCLIP

# Debugging
if DEBUG:
    all_variables = dir()

    for name in all_variables:
        # Print the item if it doesn't start with '__'
        if not name.startswith("__"):
            myvalue = eval(name)
            print(name, "is", type(myvalue), "and = ", myvalue)


client = VDMS_Client(VDMS_HOST, VDMS_PORT)


@register_microservice(
    name="opea_service@retriever_vdms",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/retrieval",
    host="0.0.0.0",
    port=7000,
)
@register_statistics(names=["opea_service@retriever_vdms"])
def retrieve(input: EmbedDoc) -> SearchedMultimodalDoc:
    start = time.time()

    if input.search_type == "similarity":
        search_res = vector_db.similarity_search_by_vector(
            embedding=input.embedding, k=input.k, filter=input.constraints
        )
    elif input.search_type == "similarity_distance_threshold":
        if input.distance_threshold is None:
            raise ValueError("distance_threshold must be provided for " + "similarity_distance_threshold retriever")
        search_res = vector_db.similarity_search_by_vector(
            embedding=input.embedding, k=input.k, distance_threshold=input.distance_threshold, filter=input.constraints
        )
    elif input.search_type == "similarity_score_threshold":
        docs_and_similarities = vector_db.similarity_search_with_relevance_scores(
            query=input.text, k=input.k, score_threshold=input.score_threshold, filter=input.constraints
        )
        search_res = [doc for doc, _ in docs_and_similarities]
    elif input.search_type == "mmr":
        search_res = vector_db.max_marginal_relevance_search(
            query=input.text, k=input.k, fetch_k=input.fetch_k, lambda_mult=input.lambda_mult, filter=input.constraints
        )
    searched_docs = []
    metadata_list = []
    for r in search_res:
        searched_docs.append(TextDoc(text=r.page_content))
        metadata_list.append(r.metadata)
    result = SearchedMultimodalDoc(retrieved_docs=searched_docs, metadata=metadata_list, initial_query=input.text)
    statistics_dict["opea_service@retriever_vdms"].append_latency(time.time() - start, None)
    return result


if __name__ == "__main__":
    # Create vectorstore

    if use_clip:
        embeddings = vCLIP({"model_name": "openai/clip-vit-base-patch32", "num_frm": 4})
        dimensions = embeddings.get_embedding_length()
    elif tei_embedding_endpoint:
        embeddings = HuggingFaceEndpointEmbeddings(model=tei_embedding_endpoint, huggingfacehub_api_token=hf_token)
    else:
        embeddings = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)
        # create embeddings using local embedding model

    if use_clip:
        vector_db = VDMS(
            client=client,
            embedding=embeddings,
            collection_name=INDEX_NAME,
            embedding_dimensions=dimensions,
            distance_strategy=DISTANCE_STRATEGY,
            engine=SEARCH_ENGINE,
        )
    else:
        vector_db = VDMS(
            client=client,
            embedding=embeddings,
            collection_name=INDEX_NAME,
            # embedding_dimensions=768,
            distance_strategy=DISTANCE_STRATEGY,
            engine=SEARCH_ENGINE,
        )

    opea_microservices["opea_service@retriever_vdms"].start()

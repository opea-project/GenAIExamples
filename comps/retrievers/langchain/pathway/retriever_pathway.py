# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from langchain_community.vectorstores import PathwayVectorClient
from langsmith import traceable

from comps import (
    EmbedDoc,
    SearchedDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

host = os.getenv("PATHWAY_HOST", "127.0.0.1")
port = int(os.getenv("PATHWAY_PORT", 8666))

EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")

tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT")


@register_microservice(
    name="opea_service@retriever_pathway",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/retrieval",
    host="0.0.0.0",
    port=7000,
)
@traceable(run_type="retriever")
@register_statistics(names=["opea_service@retriever_pathway"])
def retrieve(input: EmbedDoc) -> SearchedDoc:
    start = time.time()
    documents = pw_client.similarity_search(input.text, input.fetch_k)

    docs = [TextDoc(text=r.page_content) for r in documents]

    time_spent = time.time() - start
    statistics_dict["opea_service@retriever_pathway"].append_latency(time_spent, None)  # noqa: E501
    return SearchedDoc(retrieved_docs=docs, initial_query=input.text)


if __name__ == "__main__":
    # Create the vectorstore client
    pw_client = PathwayVectorClient(host=host, port=port)
    opea_microservices["opea_service@retriever_pathway"].start()

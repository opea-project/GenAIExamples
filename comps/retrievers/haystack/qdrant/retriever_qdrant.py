# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from haystack.components.embedders import HuggingFaceTEITextEmbedder, SentenceTransformersTextEmbedder
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from langsmith import traceable
from qdrant_config import EMBED_DIMENSION, EMBED_ENDPOINT, EMBED_MODEL, INDEX_NAME, QDRANT_HOST, QDRANT_PORT

from comps import EmbedDoc768, SearchedDoc, ServiceType, TextDoc, opea_microservices, register_microservice


# Create a pipeline for querying a Qdrant document store
def initialize_qdrant_retriever() -> QdrantEmbeddingRetriever:
    qdrant_store = QdrantDocumentStore(
        host=QDRANT_HOST, port=QDRANT_PORT, embedding_dim=EMBED_DIMENSION, index=INDEX_NAME, recreate_index=False
    )

    retriever = QdrantEmbeddingRetriever(document_store=qdrant_store)

    return retriever


@register_microservice(
    name="opea_service@retriever_qdrant",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/retrieval",
    host="0.0.0.0",
    port=7000,
)
@traceable(run_type="retriever")
def retrieve(input: EmbedDoc768) -> SearchedDoc:
    search_res = retriever.run(query_embedding=input.embedding)["documents"]
    searched_docs = [TextDoc(text=r.content) for r in search_res]
    result = SearchedDoc(retrieved_docs=searched_docs, initial_query=input.text)
    return result


if __name__ == "__main__":
    if EMBED_ENDPOINT:
        # create embeddings using TEI endpoint service
        embedder = HuggingFaceTEITextEmbedder(url=EMBED_ENDPOINT)
    else:
        # create embeddings using local embedding model
        embedder = SentenceTransformersTextEmbedder(model=EMBED_MODEL)
        embedder.warm_up()

    retriever = initialize_qdrant_retriever()
    opea_microservices["opea_service@retriever_qdrant"].start()

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os

from elasticsearch import Elasticsearch
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_elasticsearch import ElasticsearchStore

from comps import CustomLogger, EmbedDoc, OpeaComponent, OpeaComponentRegistry, ServiceType

from .config import EMBED_MODEL, ES_CONNECTION_STRING, ES_INDEX_NAME, TEI_EMBEDDING_ENDPOINT

logger = CustomLogger("es_retrievers")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_RETRIEVER_ELASTICSEARCH")
class OpeaElasticsearchRetriever(OpeaComponent):
    """A specialized retriever component derived from OpeaComponent for elasticsearch retriever services.

    Attributes:
        client (Elasticsearch): An instance of the elasticsearch client for vector database operations.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.RETRIEVER.name.lower(), description, config)

        self.embedder = self._initialize_embedder()
        self.es_connection_string = ES_CONNECTION_STRING
        self.es_index_name = ES_INDEX_NAME
        self.client, self.store = self._initialize_client()
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaElasticsearchRetriever health check failed.")

    def _initialize_embedder(self):
        if TEI_EMBEDDING_ENDPOINT:
            # create embeddings using TEI endpoint service
            if logflag:
                logger.info(f"[ init embedder ] TEI_EMBEDDING_ENDPOINT:{TEI_EMBEDDING_ENDPOINT}")
            embeddings = HuggingFaceHubEmbeddings(model=TEI_EMBEDDING_ENDPOINT)
        else:
            # create embeddings using local embedding model
            if logflag:
                logger.info(f"[ init embedder ] LOCAL_EMBEDDING_MODEL:{EMBED_MODEL}")
            embeddings = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)
        return embeddings

    def _initialize_client(self) -> Elasticsearch:
        """Initializes the elasticsearch client."""
        es_client = Elasticsearch(hosts=ES_CONNECTION_STRING)
        es_store = ElasticsearchStore(index_name=self.es_index_name, embedding=self.embedder, es_connection=es_client)
        return es_client, es_store

    def check_health(self) -> bool:
        """Checks the health of the retriever service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        if logflag:
            logger.info("[ check health ] start to check health of elasticsearch")
        try:
            if not self.client.indices.exists(index=self.es_index_name):
                self.client.indices.create(index=self.es_index_name)
            logger.info("[ check health ] Successfully connected to Elasticsearch!")
            return True
        except Exception as e:
            logger.info(f"[ check health ] Failed to connect to Elasticsearch: {e}")
            return False

    async def invoke(self, input: EmbedDoc) -> list:
        """Search the Elasticsearch index for the most similar documents to the input query.

        Args:
            input (EmbedDoc): The input query to search for.
        Output:
            list: The retrieved documents.
        """
        if logflag:
            logger.info(input)

        if input.search_type == "similarity":
            docs_and_similarities = self.store.similarity_search_by_vector_with_relevance_scores(
                embedding=input.embedding, k=input.k
            )
            search_res = [doc for doc, _ in docs_and_similarities]

        elif input.search_type == "similarity_distance_threshold":
            if input.distance_threshold is None:
                raise ValueError("distance_threshold must be provided for " + "similarity_distance_threshold retriever")
            docs_and_similarities = self.store.similarity_search_by_vector_with_relevance_scores(
                embedding=input.embedding, k=input.k
            )
            search_res = [doc for doc, similarity in docs_and_similarities if similarity > input.distance_threshold]

        elif input.search_type == "similarity_score_threshold":
            docs_and_similarities = self.store.similarity_search_by_vector_with_relevance_scores(
                query=input.text, k=input.k
            )
            search_res = [doc for doc, similarity in docs_and_similarities if similarity > input.score_threshold]

        elif input.search_type == "mmr":
            search_res = self.store.max_marginal_relevance_search(
                query=input.text, k=input.k, fetch_k=input.fetch_k, lambda_mult=input.lambda_mult
            )

        else:
            raise ValueError(f"search type {input.search_type} not valid")

        if logflag:
            logger.info(f"retrieve result: {search_res}")

        return search_res

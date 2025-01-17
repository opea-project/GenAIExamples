# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os
from typing import Callable, List, Union

import numpy as np
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from pydantic import conlist

from comps import CustomLogger, EmbedDoc, OpeaComponent, OpeaComponentRegistry, ServiceType
from comps.cores.proto.api_protocol import ChatCompletionRequest, RetrievalRequest

from .config import (
    EMBED_MODEL,
    OPENSEARCH_INDEX_NAME,
    OPENSEARCH_INITIAL_ADMIN_PASSWORD,
    OPENSEARCH_URL,
    TEI_EMBEDDING_ENDPOINT,
)

logger = CustomLogger("opensearch_retrievers")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_RETRIEVER_OPENSEARCH")
class OpeaOpensearchRetriever(OpeaComponent):
    """A specialized retriever component derived from OpeaComponent for opensearch retriever services.

    Attributes:
        client (Opensearch): An instance of the opensearch client for vector database operations.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.RETRIEVER.name.lower(), description, config)

        self.embedder = self._initialize_embedder()
        self.opensearch_url = OPENSEARCH_URL
        self.opensearch_index_name = OPENSEARCH_INDEX_NAME
        self.vector_db = self._initialize_client()
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaOpensearchRetriever health check failed.")

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

    def _initialize_client(self):
        """Initializes the opensearch client."""
        auth = ("admin", OPENSEARCH_INITIAL_ADMIN_PASSWORD)
        vector_db = OpenSearchVectorSearch(
            opensearch_url=self.opensearch_url,
            index_name=self.opensearch_index_name,
            embedding_function=self.embedder,
            http_auth=auth,
            use_ssl=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )
        return vector_db

    def check_health(self) -> bool:
        """Checks the health of the retriever service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        if logflag:
            logger.info("[ check health ] start to check health of opensearch")
        try:
            _ = self.vector_db.client.indices.exists(index=self.opensearch_index_name)
            logger.info("[ check health ] Successfully connected to Opensearch!")
            return True
        except Exception as e:
            logger.info(f"[ check health ] Failed to connect to Opensearch: {e}")
            return False

    async def invoke(self, input: Union[EmbedDoc, RetrievalRequest, ChatCompletionRequest]) -> list:
        """Search the Opensearch index for the most similar documents to the input query.

        Args:
            input (EmbedDoc): The input query to search for.
        Output:
            list: The retrieved documents.
        """
        if logflag:
            logger.info(input)

        index_exists = self.vector_db.client.indices.exists(index=self.opensearch_index_name)
        if index_exists:
            doc_count = self.vector_db.client.count(index=self.opensearch_index_name)["count"]
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
                search_res = await self.search_all_embeddings_vectors(
                    embeddings=input.embedding,
                    func=self.vector_db.asimilarity_search_by_vector,
                    k=input.k,
                )
            elif input.search_type == "similarity_distance_threshold":
                if input.distance_threshold is None:
                    raise ValueError(
                        "distance_threshold must be provided for " + "similarity_distance_threshold retriever"
                    )
                search_res = await self.search_all_embeddings_vectors(
                    embeddings=input.embedding,
                    func=self.vector_db.asimilarity_search_by_vector,
                    k=input.k,
                    distance_threshold=input.distance_threshold,
                )
            elif input.search_type == "similarity_score_threshold":
                doc_and_similarities = await self.vector_db.asimilarity_search_with_relevance_scores(
                    query=query, k=input.k, score_threshold=input.score_threshold
                )
                search_res = [doc for doc, _ in doc_and_similarities]
            elif input.search_type == "mmr":
                search_res = await self.vector_db.amax_marginal_relevance_search(
                    query=query, k=input.k, fetch_k=input.fetch_k, lambda_mult=input.lambda_mult
                )
            else:
                raise ValueError(f"{input.search_type} not valid")

        if logflag:
            logger.info(f"retrieve result: {search_res}")

        return search_res

    async def search_all_embeddings_vectors(
        self,
        embeddings: Union[conlist(float, min_length=0), List[conlist(float, min_length=0)]],
        func: Callable,
        *args,
        **kwargs,
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

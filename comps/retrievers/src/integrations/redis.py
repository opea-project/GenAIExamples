# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os
from typing import Union

from langchain_community.vectorstores import Redis

from comps import (
    CustomLogger,
    EmbedDoc,
    EmbedMultimodalDoc,
    OpeaComponent,
    OpeaComponentRegistry,
    SearchedDoc,
    ServiceType,
)
from comps.cores.proto.api_protocol import ChatCompletionRequest, EmbeddingResponse, RetrievalRequest, RetrievalResponse

from .config import BRIDGE_TOWER_EMBEDDING, EMBED_MODEL, INDEX_NAME, REDIS_URL, TEI_EMBEDDING_ENDPOINT

logger = CustomLogger("redis_retrievers")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_RETRIEVER_REDIS")
class OpeaRedisRetriever(OpeaComponent):
    """A specialized retriever component derived from OpeaComponent for redis retriever services.

    Attributes:
        client (redis.Redis): An instance of the redis client for vector database operations.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.RETRIEVER.name.lower(), description, config)

        # Create embeddings
        if TEI_EMBEDDING_ENDPOINT:
            # create embeddings using TEI endpoint service
            from langchain_huggingface import HuggingFaceEndpointEmbeddings

            self.embeddings = HuggingFaceEndpointEmbeddings(model=TEI_EMBEDDING_ENDPOINT)
        elif BRIDGE_TOWER_EMBEDDING:
            logger.info("use bridge tower embedding")
            from comps.third_parties.bridgetower.src.bridgetower_embedding import BridgeTowerEmbedding

            self.embeddings = BridgeTowerEmbedding()
        else:
            # create embeddings using local embedding model
            from langchain_community.embeddings import HuggingFaceBgeEmbeddings

            self.embeddings = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)
        self.client = self._initialize_client()
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaRedisRetriever health check failed.")

    def _initialize_client(self) -> Redis:
        """Initializes the redis client."""
        try:
            client = Redis(embedding=self.embeddings, index_name=INDEX_NAME, redis_url=REDIS_URL)
            return client
        except Exception as e:
            logger.error(f"fail to initialize redis client: {e}")
            return None

    def check_health(self) -> bool:
        """Checks the health of the retriever service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        if logflag:
            logger.info("[ health check ] start to check health of redis")
        try:
            if self.client.client.ping():
                if logflag:
                    logger.info("[ health check ] Successfully connected to Redis!")
                return True
        except Exception as e:
            logger.info(f"[ health check ] Failed to connect to Redis: {e}")
            return False

    async def invoke(
        self, input: Union[EmbedDoc, EmbedMultimodalDoc, RetrievalRequest, ChatCompletionRequest]
    ) -> Union[SearchedDoc, RetrievalResponse, ChatCompletionRequest]:
        """Search the Redis index for the most similar documents to the input query.

        Args:
            input (Union[EmbedDoc, RetrievalRequest, ChatCompletionRequest]): The input query to search for.
        Output:
            Union[SearchedDoc, RetrievalResponse, ChatCompletionRequest]: The retrieved documents.
        """
        if logflag:
            logger.info(input)

        # check if the Redis index has data
        if self.client.client.keys() == []:
            search_res = []
        else:
            if isinstance(input, EmbedDoc) or isinstance(input, EmbedMultimodalDoc):
                embedding_data_input = input.embedding
            else:
                # for RetrievalRequest, ChatCompletionRequest
                if isinstance(input.embedding, EmbeddingResponse):
                    embeddings = input.embedding.data
                    embedding_data_input = []
                    for emb in embeddings:
                        embedding_data_input.append(emb.embedding)
                else:
                    embedding_data_input = input.embedding

            # if the Redis index has data, perform the search
            if input.search_type == "similarity":
                search_res = await self.client.asimilarity_search_by_vector(embedding=embedding_data_input, k=input.k)
            elif input.search_type == "similarity_distance_threshold":
                if input.distance_threshold is None:
                    raise ValueError(
                        "distance_threshold must be provided for " + "similarity_distance_threshold retriever"
                    )
                search_res = await self.client.asimilarity_search_by_vector(
                    embedding=input.embedding, k=input.k, distance_threshold=input.distance_threshold
                )
            elif input.search_type == "similarity_score_threshold":
                docs_and_similarities = await self.client.asimilarity_search_with_relevance_scores(
                    query=input.text, k=input.k, score_threshold=input.score_threshold
                )
                search_res = [doc for doc, _ in docs_and_similarities]
            elif input.search_type == "mmr":
                search_res = await self.client.amax_marginal_relevance_search(
                    query=input.text, k=input.k, fetch_k=input.fetch_k, lambda_mult=input.lambda_mult
                )
            else:
                raise ValueError(f"{input.search_type} not valid")

        if logflag:
            logger.info(search_res)

        return search_res

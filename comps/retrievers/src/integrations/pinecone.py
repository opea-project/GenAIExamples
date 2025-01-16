# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os
import time

from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from comps import CustomLogger, EmbedDoc, OpeaComponent, OpeaComponentRegistry, ServiceType

from .config import EMBED_MODEL, PINECONE_API_KEY, PINECONE_INDEX_NAME, TEI_EMBEDDING_ENDPOINT

logger = CustomLogger("pinecone_retrievers")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_RETRIEVER_PINECONE")
class OpeaPineconeRetriever(OpeaComponent):
    """A specialized retriever component derived from OpeaComponent for pinecone retriever services.

    Attributes:
        client (Pinecone): An instance of the pinecone client for vector database operations.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.RETRIEVER.name.lower(), description, config)

        self.embedder = self._initialize_embedder()
        self.pinecone_api_key = PINECONE_API_KEY
        self.pinecone_index = PINECONE_INDEX_NAME
        self.pc, self.index, self.vector_db = self._initialize_client()
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaPineconeRetriever health check failed.")

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

    def _initialize_client(self) -> Pinecone:
        """Initializes the pinecone client."""
        pc = Pinecone(api_key=self.pinecone_api_key)
        spec = ServerlessSpec(cloud="aws", region="us-east-1")
        existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
        if self.pinecone_index in existing_indexes:
            pc.configure_index(self.pinecone_index, deletion_protection="disabled")
            pc.delete_index(self.pinecone_index)
            time.sleep(1)

        pc.create_index(
            self.pinecone_index,
            dimension=768,
            deletion_protection="disabled",
            spec=spec,
        )
        while not pc.describe_index(self.pinecone_index).status["ready"]:
            time.sleep(1)

        index = pc.Index(self.pinecone_index)
        vector_db = PineconeVectorStore(index=index, embedding=self.embedder)
        return pc, index, vector_db

    def check_health(self) -> bool:
        """Checks the health of the retriever service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        if logflag:
            logger.info("[ check health ] start to check health of pinecone")
        try:
            health_status = self.index.describe_index_stats()
            logger.info(f"[ check health ] health status: {health_status}")
            logger.info("[ check health ] Successfully connected to Pinecone!")
            return True
        except Exception as e:
            logger.info(f"[ check health ] Failed to connect to Pinecone: {e}")
            return False

    async def invoke(self, input: EmbedDoc) -> list:
        """Search the Pinecone index for the most similar documents to the input query.

        Args:
            input (EmbedDoc): The input query to search for.
        Output:
            list: The retrieved documents.
        """
        if logflag:
            logger.info(input)

        # return empty result if the index has no data
        if self.index.describe_index_stats()["total_vector_count"] == 0:
            if logflag:
                logger.info("[ invoke ] Pinecone index has no data.")
            return []

        # perform the search
        search_res = self.vector_db.max_marginal_relevance_search(query=input.text, k=input.k, fetch_k=input.fetch_k)
        # if the Pinecone index has data, perform the search
        if input.search_type == "similarity":
            docs_and_similarities = self.vector_db.similarity_search_by_vector_with_score(
                embedding=input.embedding, k=input.k
            )
            search_res = [doc for doc, _ in docs_and_similarities]
        elif input.search_type == "similarity_distance_threshold":
            if input.distance_threshold is None:
                raise ValueError("distance_threshold must be provided for " + "similarity_distance_threshold retriever")
            docs_and_similarities = self.vector_db.similarity_search_by_vector_with_score(
                embedding=input.embedding, k=input.k
            )
            search_res = [doc for doc, similarity in docs_and_similarities if similarity > input.distance_threshold]
        elif input.search_type == "similarity_score_threshold":
            docs_and_similarities = self.vector_db.similarity_search_by_vector_with_score(query=input.text, k=input.k)
            search_res = [doc for doc, similarity in docs_and_similarities if similarity > input.score_threshold]
        elif input.search_type == "mmr":
            search_res = self.vector_db.max_marginal_relevance_search(
                query=input.text, k=input.k, fetch_k=input.fetch_k, lambda_mult=input.lambda_mult
            )

        if logflag:
            logger.info(f"retrieve result: {search_res}")

        return search_res

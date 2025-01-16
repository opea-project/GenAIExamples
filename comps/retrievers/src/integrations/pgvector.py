# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os

from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores import PGVector

from comps import CustomLogger, EmbedDoc, OpeaComponent, OpeaComponentRegistry, ServiceType

from .config import EMBED_MODEL, PG_CONNECTION_STRING, PG_INDEX_NAME, TEI_EMBEDDING_ENDPOINT

logger = CustomLogger("pgvector_retrievers")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_RETRIEVER_PGVECTOR")
class OpeaPGVectorRetriever(OpeaComponent):
    """A specialized retriever component derived from OpeaComponent for pgvector retriever services.

    Attributes:
        client (PGVector): An instance of the pgvector client for vector database operations.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.RETRIEVER.name.lower(), description, config)

        self.embedder = self._initialize_embedder()
        self.pg_connection_string = PG_CONNECTION_STRING
        self.pg_index_name = PG_INDEX_NAME
        self.vector_db = self._initialize_client()
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaPGVectorRetriever health check failed.")

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

    def _initialize_client(self) -> PGVector:
        """Initializes the pgvector client."""
        vector_db = PGVector(
            embedding_function=self.embedder,
            collection_name=self.pg_index_name,
            connection_string=self.pg_connection_string,
        )
        return vector_db

    def check_health(self) -> bool:
        """Checks the health of the retriever service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        if logflag:
            logger.info("[ check health ] start to check health of PGvector")
        try:
            # Check the status of the PGVector service
            self.vector_db.create_collection()
            logger.info("[ check health ] Successfully connected to PGvector!")
            return True
        except Exception as e:
            logger.info(f"[ check health ] Failed to connect to PGvector: {e}")
            return False

    async def invoke(self, input: EmbedDoc) -> list:
        """Search the PGVector index for the most similar documents to the input query.

        Args:
            input (EmbedDoc): The input query to search for.
        Output:
            list: The retrieved documents.
        """
        if logflag:
            logger.info(f"[ similarity search ] input: {input}")

        search_res = await self.vector_db.asimilarity_search_by_vector(embedding=input.embedding)

        if logflag:
            logger.info(f"[ similarity search ] search result: {search_res}")
        return search_res

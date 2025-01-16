# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os

from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from comps import CustomLogger, EmbedDoc, OpeaComponent, OpeaComponentRegistry, ServiceType

from .config import QDRANT_EMBED_DIMENSION, QDRANT_HOST, QDRANT_INDEX_NAME, QDRANT_PORT

logger = CustomLogger("qdrant_retrievers")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_RETRIEVER_QDRANT")
class OpeaQDrantRetriever(OpeaComponent):
    """A specialized retriever component derived from OpeaComponent for qdrant retriever services.

    Attributes:
        client (QDrant): An instance of the qdrant client for vector database operations.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.RETRIEVER.name.lower(), description, config)

        self.retriever = self._initialize_client()
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaQDrantRetriever health check failed.")

    def _initialize_client(self) -> QdrantEmbeddingRetriever:
        """Initializes the qdrant client."""
        qdrant_store = QdrantDocumentStore(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            embedding_dim=QDRANT_EMBED_DIMENSION,
            index=QDRANT_INDEX_NAME,
            recreate_index=False,
        )

        retriever = QdrantEmbeddingRetriever(document_store=qdrant_store)

        return retriever

    def check_health(self) -> bool:
        """Checks the health of the retriever service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        if logflag:
            logger.info("[ check health ] start to check health of QDrant")
        try:
            # Check the status of the QDrant service
            _ = self.retriever.client
            logger.info("[ check health ] Successfully connected to QDrant!")
            return True
        except Exception as e:
            logger.info(f"[ check health ] Failed to connect to QDrant: {e}")
            return False

    async def invoke(self, input: EmbedDoc) -> list:
        """Search the QDrant index for the most similar documents to the input query.

        Args:
            input (EmbedDoc): The input query to search for.
        Output:
            list: The retrieved documents.
        """
        if logflag:
            logger.info(f"[ similarity search ] input: {input}")

        search_res = self.retriever.run(query_embedding=input.embedding)["documents"]

        if logflag:
            logger.info(f"[ similarity search ] search result: {search_res}")
        return search_res

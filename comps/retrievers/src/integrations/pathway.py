# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os

from langchain_community.vectorstores import PathwayVectorClient

from comps import CustomLogger, EmbedDoc, OpeaComponent, OpeaComponentRegistry, SearchedDoc, ServiceType

from .config import PATHWAY_HOST, PATHWAY_PORT

logger = CustomLogger("pathway_retrievers")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_RETRIEVER_PATHWAY")
class OpeaPathwayRetriever(OpeaComponent):
    """A specialized retriever component derived from OpeaComponent for pathway retriever services.

    Attributes:
        client (Pathway): An instance of the pathway client for vector database operations.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.RETRIEVER.name.lower(), description, config)

        self.host = PATHWAY_HOST
        self.port = PATHWAY_PORT
        self.client = self._initialize_client()
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaPathwayRetriever health check failed.")

    def _initialize_client(self) -> PathwayVectorClient:
        """Initializes the pathway client."""
        pw_client = PathwayVectorClient(host=self.host, port=self.port)

        return pw_client

    def check_health(self) -> bool:
        """Checks the health of the retriever service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        if logflag:
            logger.info("[ check health ] start to check health of Pathway")
        try:
            # Check the status of the Pathway service
            _ = self.client.client
            logger.info("[ check health ] Successfully connected to Pathway!")
            return True
        except Exception as e:
            logger.info(f"[ check health ] Failed to connect to Pathway: {e}")
            return False

    async def invoke(self, input: EmbedDoc) -> SearchedDoc:
        """Search the Pathway index for the most similar documents to the input query.

        Args:
            input (EmbedDoc): The input query to search for.
        Output:
            Union[SearchedDoc, RetrievalResponse, ChatCompletionRequest]: The retrieved documents.
        """
        if logflag:
            logger.info(f"[ similarity search ] input: {input}")

        search_res = self.client.similarity_search(input.text, input.fetch_k)

        if logflag:
            logger.info(f"[ similarity search ] search result: {search_res}")
        return search_res

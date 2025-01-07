# Copyright (C) 2024 Prediction Guard, Inc.
# SPDX-License-Identified: Apache-2.0

import asyncio
import os

from predictionguard import PredictionGuard

from comps import CustomLogger, OpeaComponent, OpeaComponentRegistry, ServiceType
from comps.cores.proto.api_protocol import EmbeddingRequest, EmbeddingResponse, EmbeddingResponseData

logger = CustomLogger("predictionguard_embedding")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_PREDICTIONGUARD_EMBEDDING")
class PredictionguardEmbedding(OpeaComponent):
    """A specialized embedding component derived from OpeaComponent for interacting with Prediction Guard services.

    Attributes:
        client (PredictionGuard): An instance of the PredictionGuard client for embedding generation.
        model_name (str): The name of the embedding model used by the Prediction Guard service.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.EMBEDDING.name.lower(), description, config)
        api_key = os.getenv("PREDICTIONGUARD_API_KEY")
        self.client = None
        if api_key:
            self.client = PredictionGuard(api_key=api_key)
        else:
            logger.info("No PredictionGuard API KEY provided, client not instantiated")
        self.model_name = os.getenv("PG_EMBEDDING_MODEL_NAME", "bridgetower-large-itm-mlm-itc")
        health_status = self.check_health()
        if not health_status:
            logger.error("PredictionguardEmbedding health check failed.")

    def check_health(self) -> bool:
        """Checks the health of the Prediction Guard embedding service.

        This function sends a request to fetch the list of embedding models
        to determine if the service is reachable and operational.

        Returns:
            bool: True if the service returns a valid model list, False otherwise.
        """
        try:
            if not self.client:
                return False
            # Send a request to retrieve the list of models
            response = self.client.embeddings.create(model="bridgetower-large-itm-mlm-itc", input=[{"text": "hello"}])

            # Check if the response is a valid dictionary and contains the expected 'model' key
            if isinstance(response, dict) and "model" in response:
                # Check if the model matches the expected model name
                if response["model"] == self.model_name:
                    return True
                else:
                    return False
            else:
                # Handle the case where the response does not have the expected structure
                return False

        except Exception as e:
            # Handle exceptions such as network errors or unexpected failures
            logger.error(f"Health check failed due to an exception: {e}")
            return False

    async def invoke(self, input: EmbeddingRequest) -> EmbeddingResponse:
        """Invokes the embedding service to generate embeddings for the provided input.

        Args:
            input (EmbeddingRequest): The input in OpenAI embedding format, including text(s) and optional parameters like model.

        Returns:
            EmbeddingResponse: The response in OpenAI embedding format, including embeddings, model, and usage information.
        """
        # Parse input according to the EmbeddingRequest format
        if isinstance(input.input, str):
            texts = [input.input.replace("\n", " ")]
        elif isinstance(input.input, list):
            if all(isinstance(item, str) for item in input.input):
                texts = [text.replace("\n", " ") for text in input.input]
            else:
                raise ValueError("Invalid input format: Only string or list of strings are supported.")
        else:
            raise TypeError("Unsupported input type: input must be a string or list of strings.")
        texts = [{"text": texts[i]} for i in range(len(texts))]
        # Run the synchronous `create` method in a separate thread
        response = await asyncio.to_thread(self.client.embeddings.create, model=self.model_name, input=texts)
        response_data = response["data"]
        embed_vector = [response_data[i]["embedding"] for i in range(len(response_data))]
        # for standard openai embedding format
        res = EmbeddingResponse(
            data=[EmbeddingResponseData(index=i, embedding=embed_vector[i]) for i in range(len(embed_vector))]
        )
        return res

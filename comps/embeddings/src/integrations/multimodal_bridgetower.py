# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import os

import requests

from comps import (
    CustomLogger,
    EmbedMultimodalDoc,
    MultimodalDoc,
    OpeaComponent,
    OpeaComponentRegistry,
    ServiceType,
    TextDoc,
    TextImageDoc,
)

logger = CustomLogger("opea_multimodal_embedding_bridgetower")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_MULTIMODAL_EMBEDDING_BRIDGETOWER")
class OpeaMultimodalEmbeddingBrigeTower(OpeaComponent):
    """A specialized embedding component derived from OpeaComponent for local deployed BrigeTower multimodal embedding services.

    Attributes:
        model_name (str): The name of the embedding model used.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.EMBEDDING.name.lower(), description, config)
        self.base_url = os.getenv("MMEI_EMBEDDING_ENDPOINT", "http://localhost:8080")
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaMultimodalEmbeddingBrigeTower health check failed.")

    async def invoke(self, input: MultimodalDoc) -> EmbedMultimodalDoc:
        """Invokes the embedding service to generate embeddings for the provided input.

        Args:
            input (Union[str, List[str]]): The input text(s) for which embeddings are to be generated.

        Returns:
            List[List[float]]: A list of embedding vectors for the input text(s).
        """
        json = {}
        if isinstance(input, TextDoc):
            json["text"] = input.text
        elif isinstance(input, TextImageDoc):
            json["text"] = input.text.text
            img_bytes = input.image.url.load_bytes()
            base64_img = base64.b64encode(img_bytes).decode("utf-8")
            json["img_b64_str"] = base64_img
        else:
            raise TypeError(
                f"Unsupported input type: {type(input)}. "
                "Input must be an instance of 'TextDoc' or 'TextImageDoc'. "
                "Please verify the input type and try again."
            )

        response = await asyncio.to_thread(
            requests.post, f"{self.base_url}/v1/encode", headers={"Content-Type": "application/json"}, json=json
        )
        response_json = response.json()
        embed_vector = response_json["embedding"]
        if isinstance(input, TextDoc):
            res = EmbedMultimodalDoc(text=input.text, embedding=embed_vector)
        elif isinstance(input, TextImageDoc):
            res = EmbedMultimodalDoc(text=input.text.text, url=input.image.url, embedding=embed_vector)

        return res

    def check_health(self) -> bool:
        """Check the health of the microservice by making a GET request to /v1/health_check."""
        try:
            response = requests.get(f"{self.base_url}/v1/health_check")
            if response.status_code == 200:
                return True
            return False
        except requests.exceptions.RequestException as e:
            logger.info(f"Health check exception: {e}")
            return False

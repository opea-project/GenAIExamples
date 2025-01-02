# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any, List

import torch
from langchain_core.embeddings import Embeddings
from langchain_core.pydantic_v1 import BaseModel, Extra
from PIL import Image
from transformers import BridgeTowerProcessor

from .bridgetower_custom import BridgeTowerForITC, BridgeTowerTextFeatureExtractor


class BridgeTowerEmbedding(BaseModel, Embeddings):
    """BridgeTower embedding model."""

    model_name: str = "BridgeTower/bridgetower-large-itm-mlm-itc"
    device: str = "cpu"
    TEXT_MODEL: Any
    PROCESSOR: Any
    MODEL: Any

    def __init__(self, **kwargs: Any):
        """Initialize the BridgeTowerEmbedding class."""
        super().__init__(**kwargs)

        if "device" in kwargs:
            if kwargs["device"] == "hpu":
                try:
                    import habana_frameworks.torch.core as htcore

                    self.device = torch.device("hpu")
                except ImportError:
                    self.device = "cpu"
            elif kwargs["device"] == "gpu":
                if torch.cuda.is_available():
                    self.device = "cuda"
            else:
                self.device = "cpu"

        self.TEXT_MODEL = BridgeTowerTextFeatureExtractor.from_pretrained(self.model_name).to(self.device)
        self.PROCESSOR = BridgeTowerProcessor.from_pretrained(self.model_name)
        self.MODEL = BridgeTowerForITC.from_pretrained(self.model_name).to(self.device)

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents using BridgeTower.

        Args:
            texts: The list of texts to embed.
        Returns:
            List of embeddings, one for each text.
        """
        encodings = self.PROCESSOR.tokenizer(
            texts, return_tensors="pt", max_length=200, padding="max_length", truncation=True
        ).to(self.device)
        with torch.no_grad():
            outputs = self.TEXT_MODEL(**encodings)
        embeddings = outputs.cpu().numpy().tolist()
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a query using BridgeTower.

        Args:
            text: The text to embed.
        Returns:
            Embeddings for the text.
        """
        return self.embed_documents([text])[0]

    def embed_image_text_pairs(self, texts: List[str], images: list[Image], batch_size=2) -> List[List[float]]:  # type: ignore
        """Embed a list of image-text pairs using BridgeTower.

        Args:
            texts: The list of texts to embed.
            images: The list of path-to-images to embed
            batch_size: the batch size to process, default to 2
        Returns:
            List of embeddings, one for each image-text pairs.
        """

        # the length of texts must be equal to the length of images
        assert len(texts) == len(images), "the number of captions should be equal to the number of images"

        image_list = []
        text_list = []
        embeddings = []
        for pil_img, text in zip(images, texts):
            # print(path_to_img)
            # img = read_image(path_to_img, mode=ImageReadMode.RGB)
            # img = transform.to_pil_image(img)

            img = pil_img.convert("RGB")
            image_list.append(img)
            text_list.append(text)
            if len(text_list) == batch_size:
                batch = self.PROCESSOR(
                    image_list, text_list, return_tensors="pt", max_length=200, padding="max_length", truncation=True
                ).to(self.device)
                with torch.no_grad():
                    batch_embeddings = self.MODEL(**batch, output_hidden_states=True)

                for i in range(len(text_list)):
                    embeddings.append(batch_embeddings.logits[i, 2, :].detach().cpu().numpy().tolist())
                image_list = []
                text_list = []
        # embedding the remaining
        if len(text_list) > 0:
            batch = self.PROCESSOR(
                image_list, text_list, return_tensors="pt", max_length=100, padding="max_length", truncation=True
            ).to(self.device)
            with torch.no_grad():
                batch_embeddings = self.MODEL(**batch, output_hidden_states=True)
            for i in range(len(text_list)):
                embeddings.append(batch_embeddings.logits[i, 2, :].detach().cpu().numpy().tolist())
            image_list = []
            text_list = []
        return embeddings

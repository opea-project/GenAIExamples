# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import torch
import torchvision.transforms as T
from decord import VideoReader, cpu
from langchain.pydantic_v1 import BaseModel, root_validator
from langchain_community.vectorstores import VDMS
from langchain_community.vectorstores.vdms import VDMS_Client
from langchain_core.embeddings import Embeddings
from PIL import Image

toPIL = T.ToPILImage()

# 'similarity', 'similarity_score_threshold' (needs threshold), 'mmr'


class vCLIPEmbeddings(BaseModel, Embeddings):
    """MeanCLIP Embeddings model."""

    model: Any

    @root_validator(allow_reuse=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that open_clip and torch libraries are installed."""
        try:
            # Use the provided model if present
            if "model" not in values:
                raise ValueError("Model must be provided during initialization.")

        except ImportError:
            raise ImportError("Please ensure CLIP model is loaded")
        return values

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        model_device = next(self.model.clip.parameters()).device
        text_features = self.model.get_text_embeddings(texts)

        return text_features.detach().numpy()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def embed_video(self, paths: List[str], **kwargs: Any) -> List[List[float]]:
        # Open images directly as PIL images

        video_features = []
        for vid_path in sorted(paths):
            # Encode the video to get the embeddings
            model_device = next(self.model.parameters()).device
            # Preprocess the video for the model
            clip_images = self.load_video_for_vclip(
                vid_path,
                num_frm=self.model.num_frm,
                max_img_size=224,
                start_time=kwargs.get("start_time", None),
                clip_duration=kwargs.get("clip_duration", None),
            )
            embeddings_tensor = self.model.get_video_embeddings([clip_images])

            # Convert tensor to list and add to the video_features list
            embeddings_list = embeddings_tensor.tolist()

            video_features.append(embeddings_list)

        return video_features

    def load_video_for_vclip(self, vid_path, num_frm=4, max_img_size=224, **kwargs):
        # Load video with VideoReader
        import decord

        decord.bridge.set_bridge("torch")
        vr = VideoReader(vid_path, ctx=cpu(0))
        fps = vr.get_avg_fps()
        num_frames = len(vr)
        start_idx = int(fps * kwargs.get("start_time", [0])[0])
        end_idx = start_idx + int(fps * kwargs.get("clip_duration", [num_frames])[0])

        frame_idx = np.linspace(start_idx, end_idx, num=num_frm, endpoint=False, dtype=int)  # Uniform sampling
        clip_images = []

        # read images
        temp_frms = vr.get_batch(frame_idx.astype(int).tolist())
        for idx in range(temp_frms.shape[0]):
            im = temp_frms[idx]  # H W C
            clip_images.append(toPIL(im.permute(2, 0, 1)))

        return clip_images


class VideoVS:
    def __init__(
        self,
        host,
        port,
        selected_db,
        video_retriever_model,
        collection_name,
        embedding_dimensions: int = 512,
        chosen_video_search_type="similarity",
    ):

        self.host = host
        self.port = port
        self.selected_db = selected_db
        self.chosen_video_search_type = chosen_video_search_type
        self.constraints = None
        self.video_collection = collection_name
        self.video_embedder = vCLIPEmbeddings(model=video_retriever_model)
        self.chosen_video_search_type = chosen_video_search_type
        self.embedding_dimensions = embedding_dimensions

        # initialize_db
        self.get_db_client()
        self.init_db()

    def get_db_client(self):

        if self.selected_db == "vdms":
            print("Connecting to VDMS db server . . .")
            self.client = VDMS_Client(host=self.host, port=self.port)

    def init_db(self):
        print("Loading db instances")
        if self.selected_db == "vdms":
            self.video_db = VDMS(
                client=self.client,
                embedding=self.video_embedder,
                collection_name=self.video_collection,
                engine="FaissFlat",
                distance_strategy="IP",
                embedding_dimensions=self.embedding_dimensions,
            )

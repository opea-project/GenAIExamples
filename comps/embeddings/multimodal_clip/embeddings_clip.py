# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import torch
import torch.nn as nn
from einops import rearrange
from transformers import AutoProcessor, AutoTokenizer, CLIPModel

model_name = "openai/clip-vit-base-patch32"

clip = CLIPModel.from_pretrained(model_name)
processor = AutoProcessor.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)


class vCLIP(nn.Module):
    def __init__(self, cfg):
        super().__init__()

        self.num_frm = cfg["num_frm"]
        self.model_name = cfg["model_name"]

    def embed_query(self, texts):
        """Input is list of texts."""
        text_inputs = tokenizer(texts, padding=True, return_tensors="pt")
        text_features = clip.get_text_features(**text_inputs)
        return text_features

    def get_embedding_length(self):
        return len(self.embed_query("sample_text"))

    def get_image_embeddings(self, images):
        """Input is list of images."""
        image_inputs = processor(images=images, return_tensors="pt")
        image_features = clip.get_image_features(**image_inputs)
        return image_features

    def get_video_embeddings(self, frames_batch):
        """Input is list of list of frames in video."""
        self.batch_size = len(frames_batch)
        vid_embs = []
        for frames in frames_batch:
            frame_embeddings = self.get_image_embeddings(frames)
            frame_embeddings = rearrange(frame_embeddings, "(b n) d -> b n d", b=len(frames_batch))
            # Normalize, mean aggregate and return normalized video_embeddings
            frame_embeddings = frame_embeddings / frame_embeddings.norm(dim=-1, keepdim=True)
            video_embeddings = frame_embeddings.mean(dim=1)
            video_embeddings = video_embeddings / video_embeddings.norm(dim=-1, keepdim=True)
            vid_embs.append(video_embeddings)
        return torch.cat(vid_embs, dim=0)

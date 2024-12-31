# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Any, Optional

from edgecraftrag.base import BaseComponent, CompType, ModelType
from llama_index.embeddings.huggingface_openvino import OpenVINOEmbedding
from llama_index.llms.openvino import OpenVINOLLM
from llama_index.postprocessor.openvino_rerank import OpenVINORerank
from pydantic import Field, model_serializer


def model_exist(model_path):
    model_dir = Path(model_path)
    return (
        model_dir.is_dir()
        and (model_dir / "openvino_model.xml").exists()
        and (model_dir / "openvino_model.bin").exists()
    )


class BaseModelComponent(BaseComponent):

    model_id: Optional[str] = Field(default="")
    model_path: Optional[str] = Field(default="")
    weight: Optional[str] = Field(default="")
    device: Optional[str] = Field(default="cpu")

    def run(self, **kwargs) -> Any:
        pass

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "type": self.comp_subtype,
            "model_id": self.model_id,
            "model_path": self.model_path,
            "weight": self.weight,
            "device": self.device,
        }
        return set


class OpenVINOEmbeddingModel(BaseModelComponent, OpenVINOEmbedding):

    def __init__(self, model_id, model_path, device, weight):
        if not model_exist(model_path):
            OpenVINOEmbedding.create_and_save_openvino_model(model_id, model_path)
        OpenVINOEmbedding.__init__(self, model_id_or_path=model_path, device=device)
        self.comp_type = CompType.MODEL
        self.comp_subtype = ModelType.EMBEDDING
        self.model_id = model_id
        self.model_path = model_path
        self.device = device
        self.weight = ""


class OpenVINORerankModel(BaseModelComponent, OpenVINORerank):

    def __init__(self, model_id, model_path, device, weight):
        if not model_exist(model_path):
            OpenVINORerank.create_and_save_openvino_model(model_id, model_path)
        OpenVINORerank.__init__(
            self,
            model_id_or_path=model_path,
            device=device,
        )
        self.comp_type = CompType.MODEL
        self.comp_subtype = ModelType.RERANKER
        self.model_id = model_id
        self.model_path = model_path
        self.device = device
        self.weight = ""


class OpenVINOLLMModel(BaseModelComponent, OpenVINOLLM):

    def __init__(self, model_id, model_path, device, weight):
        OpenVINOLLM.__init__(
            self,
            model_id_or_path=model_path,
            device_map=device,
        )
        self.comp_type = CompType.MODEL
        self.comp_subtype = ModelType.LLM
        self.model_id = model_id
        self.model_path = model_path
        self.device = device
        self.weight = weight

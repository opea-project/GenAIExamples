# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio

from edgecraftrag.api_schema import ModelIn
from edgecraftrag.base import BaseComponent, BaseMgr, CompType, ModelType
from edgecraftrag.components.model import (
    BaseModelComponent,
    OpenVINOEmbeddingModel,
    OpenVINOLLMModel,
    OpenVINORerankModel,
)


class ModelMgr(BaseMgr):

    def __init__(self):
        self._lock = asyncio.Lock()
        super().__init__()

    def get_model_by_name(self, name: str):
        for _, v in self.components.items():
            if v.model_id == name:
                model_type = v.comp_subtype.value
                model_info = {
                    "model_type": model_type,
                    "model_id": getattr(v, "model_id", "Unknown"),
                }
                if model_type == ModelType.LLM:
                    model_info["model_path"] = getattr(v, "model_name", "Unknown")
                    model_info["device"] = getattr(v, "device_map", "Unknown")
                else:
                    model_info["model_path"] = getattr(v, "model_id_or_path", "Unknown")
                    model_info["device"] = getattr(v, "device", getattr(v, "_device", "Unknown"))
                return model_info
        return None

    def get_models(self):
        model = {}
        for k, v in self.components.items():
            # Supplement the information of the model
            model_type = v.comp_subtype.value
            model_info = {
                "model_type": model_type,
                "model_id": getattr(v, "model_id", "Unknown"),
            }
            if model_type == ModelType.LLM:
                model_info["model_path"] = getattr(v, "model_name", "Unknown")
                model_info["device"] = getattr(v, "device_map", "Unknown")
            else:
                model_info["model_path"] = getattr(v, "model_id_or_path", "Unknown")
                model_info["device"] = getattr(v, "device", getattr(v, "_device", "Unknown"))
            model[k] = model_info
        return model

    def search_model(self, modelin: ModelIn) -> BaseComponent:
        # Compare model_path and device to search model
        for _, v in self.components.items():
            model_path = v.model_name if v.comp_subtype.value == "llm" else v.model_id_or_path
            model_dev = (
                v.device_map
                if v.comp_subtype.value == "llm"
                else getattr(v, "device", getattr(v, "_device", "Unknown"))
            )
            if model_path == modelin.model_path and model_dev == modelin.device:
                return v
        return None

    def del_model_by_name(self, name: str):
        for key, v in self.components.items():
            if v and v.model_id == name:
                self.remove(key)
                return "Model deleted"
        return "Model not found"

    @staticmethod
    def load_model(model_para: ModelIn):
        model = None
        match model_para.model_type:
            case ModelType.EMBEDDING:
                model = OpenVINOEmbeddingModel(
                    model_id=model_para.model_id,
                    model_path=model_para.model_path,
                    device=model_para.device,
                    weight=model_para.weight,
                )
            case ModelType.RERANKER:
                model = OpenVINORerankModel(
                    model_id=model_para.model_id,
                    model_path=model_para.model_path,
                    device=model_para.device,
                    weight=model_para.weight,
                )
            case ModelType.LLM:
                model = OpenVINOLLMModel(
                    model_id=model_para.model_id,
                    model_path=model_para.model_path,
                    device=model_para.device,
                    weight=model_para.weight,
                )
            case ModelType.VLLM:
                model = BaseModelComponent(model_id=model_para.model_id, model_path="", device="", weight="")
                model.comp_type = CompType.MODEL
                model.comp_subtype = ModelType.VLLM
                model.model_id_or_path = model_para.model_id
        return model

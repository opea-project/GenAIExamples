from edgecraftrag.base import (
    BaseComponent,
    CompType,
    ModelType,
)
from typing import Any
from llama_index.embeddings.huggingface_openvino import OpenVINOEmbedding
from llama_index.postprocessor.openvino_rerank import OpenVINORerank
from llama_index.llms.openvino import OpenVINOLLM
from pydantic import Field, model_serializer


class BaseModelComponent(BaseComponent):

    model_id: str = Field(default="")
    model_path: str = Field(default="")
    device: str = Field(default="")

    def run(self, **kwargs) -> Any:
        pass

    @model_serializer
    def ser_model(self):
        ser = {
            'idx': self.idx,
            'type': self.comp_subtype,
            'model_id': self.model_id,
            'model_path': self.model_path,
            'device': self.device
        }
        return ser


class OpenVINOEmbeddingModel(BaseModelComponent, OpenVINOEmbedding):

    def __init__(self, model_id, model_path, device):
        OpenVINOEmbedding.create_and_save_openvino_model(
            model_id, model_path
        )
        OpenVINOEmbedding.__init__(
            self,
            model_id_or_path=model_path,
            device=device
        )
        self.comp_type = CompType.MODEL
        self.comp_subtype = ModelType.EMBEDDING
        self.model_id = model_id
        self.model_path = model_path
        self.device = device


class OpenVINORerankModel(BaseModelComponent, OpenVINORerank):

    def __init__(self, model_id, model_path, device):
        OpenVINORerank.create_and_save_openvino_model(
            model_id, model_path
        )
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


class OpenVINOLLMModel(BaseModelComponent, OpenVINOLLM):

    def __init__(self, model_id, model_path, device):
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

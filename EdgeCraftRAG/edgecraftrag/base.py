# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import abc
import uuid
from enum import Enum
from typing import Any, Callable, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_serializer


class CompType(str, Enum):

    DEFAULT = "default"
    MODEL = "model"
    PIPELINE = "pipeline"
    NODEPARSER = "node_parser"
    INDEXER = "indexer"
    RETRIEVER = "retriever"
    POSTPROCESSOR = "postprocessor"
    GENERATOR = "generator"
    FILE = "file"


class ModelType(str, Enum):

    EMBEDDING = "embedding"
    RERANKER = "reranker"
    LLM = "llm"
    VLLM = "vllm"


class FileType(str, Enum):
    TEXT = "text"
    VISUAL = "visual"
    AURAL = "aural"
    VIRTUAL = "virtual"
    OTHER = "other"


class NodeParserType(str, Enum):

    SIMPLE = "simple"
    HIERARCHY = "hierarchical"
    SENTENCEWINDOW = "sentencewindow"
    UNSTRUCTURED = "unstructured"


class IndexerType(str, Enum):

    FAISS_VECTOR = "faiss_vector"
    DEFAULT_VECTOR = "vector"


class RetrieverType(str, Enum):

    VECTORSIMILARITY = "vectorsimilarity"
    AUTOMERGE = "auto_merge"
    BM25 = "bm25"


class PostProcessorType(str, Enum):

    RERANKER = "reranker"
    METADATAREPLACE = "metadata_replace"


class GeneratorType(str, Enum):

    CHATQNA = "chatqna"


class InferenceType(str, Enum):

    LOCAL = "local"
    VLLM = "vllm"


class CallbackType(str, Enum):

    DATAPREP = "dataprep"
    DATAUPDATE = "dataupdate"
    RETRIEVE = "retrieve"
    PIPELINE = "pipeline"


class BaseComponent(BaseModel):

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    idx: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = Field(default="")
    comp_type: str = Field(default="")
    comp_subtype: Optional[str] = Field(default="")

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "name": self.name,
            "comp_type": self.comp_type,
            "comp_subtype": self.comp_subtype,
        }
        return set

    @abc.abstractmethod
    def run(self, **kwargs) -> Any:
        pass


class BaseMgr:

    def __init__(self):
        self.components = {}

    def add(self, comp: BaseComponent):
        self.components[comp.idx] = comp

    def get(self, idx: str) -> BaseComponent:
        if idx in self.components:
            return self.components[idx]
        else:
            return None

    def remove(self, idx):
        # remove the reference count
        # after reference count == 0, object memory can be freed with Garbage Collector
        del self.components[idx]

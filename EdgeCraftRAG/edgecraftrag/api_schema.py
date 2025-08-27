# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Optional

from pydantic import BaseModel


class ModelIn(BaseModel):
    model_type: Optional[str] = "LLM"
    model_id: Optional[str]
    model_path: Optional[str] = "./"
    weight: Optional[str] = "INT4"
    device: Optional[str] = "cpu"


class NodeParserIn(BaseModel):
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunk_sizes: Optional[list] = None
    parser_type: str
    window_size: Optional[int] = 3


class IndexerIn(BaseModel):
    indexer_type: str
    embedding_model: Optional[ModelIn] = None
    vector_uri: Optional[str] = None


class RetrieverIn(BaseModel):
    retriever_type: str
    retrieve_topk: Optional[int] = 3


class PostProcessorIn(BaseModel):
    processor_type: str
    reranker_model: Optional[ModelIn] = None
    top_n: Optional[int] = 5


class GeneratorIn(BaseModel):
    prompt_path: Optional[str] = None
    prompt_content: Optional[str] = None
    model: Optional[ModelIn] = None
    inference_type: Optional[str] = "local"
    vllm_endpoint: Optional[str] = None


class PipelineCreateIn(BaseModel):
    name: Optional[str] = None
    node_parser: Optional[NodeParserIn] = None
    indexer: Optional[IndexerIn] = None
    retriever: Optional[RetrieverIn] = None
    postprocessor: Optional[list[PostProcessorIn]] = None
    generator: Optional[GeneratorIn] = None
    active: Optional[bool] = False


class DataIn(BaseModel):
    text: Optional[str] = None
    local_path: Optional[str] = None


class FilesIn(BaseModel):
    local_paths: Optional[list[str]] = None


class RagOut(BaseModel):
    query: str
    contexts: Optional[dict[str, Any]] = None
    response: str


class PromptIn(BaseModel):
    prompt: Optional[str] = None


class KnowledgeBaseCreateIn(BaseModel):
    name: str
    description: Optional[str] = None
    active: Optional[bool] = None
    comp_type: Optional[str] = "knowledge"
    experience_active:  Optional[bool] = None

class ExperienceIn(BaseModel):
    question: str
    content: list[str] = None

class MilvusConnectRequest(BaseModel):
    vector_uri: str

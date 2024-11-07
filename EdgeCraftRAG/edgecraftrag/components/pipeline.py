# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Callable, List, Optional

from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.base import BaseComponent, CallbackType, CompType, InferenceType
from edgecraftrag.components.postprocessor import RerankProcessor
from llama_index.core.schema import Document, QueryBundle
from pydantic import BaseModel, Field, model_serializer


class PipelineStatus(BaseModel):
    active: bool = False


class Pipeline(BaseComponent):

    node_parser: Optional[BaseComponent] = Field(default=None)
    indexer: Optional[BaseComponent] = Field(default=None)
    retriever: Optional[BaseComponent] = Field(default=None)
    postprocessor: Optional[List[BaseComponent]] = Field(default=None)
    generator: Optional[BaseComponent] = Field(default=None)
    status: PipelineStatus = Field(default=PipelineStatus())
    run_pipeline_cb: Optional[Callable[..., Any]] = Field(default=None)
    run_retriever_cb: Optional[Callable[..., Any]] = Field(default=None)
    run_data_prepare_cb: Optional[Callable[..., Any]] = Field(default=None)

    def __init__(
        self,
        name,
    ):
        super().__init__(name=name, comp_type=CompType.PIPELINE)
        if self.name == "" or self.name is None:
            self.name = self.idx
        self.run_pipeline_cb = run_test_generator
        self.run_retriever_cb = run_test_retrieve
        self.run_data_prepare_cb = run_simple_doc
        self._node_changed = True

    # TODO: consider race condition
    @property
    def node_changed(self) -> bool:
        return self._node_changed

    # TODO: update doc changes
    # TODO: more operations needed, add, del, modify
    def update_nodes(self, nodes):
        print("updating nodes ", nodes)
        if self.indexer is not None:
            self.indexer.insert_nodes(nodes)

    # TODO: check more conditions
    def check_active(self, nodelist):
        if self._node_changed and nodelist is not None:
            self.update_nodes(nodelist)

    # Implement abstract run function
    # callback dispatcher
    def run(self, **kwargs) -> Any:
        print(kwargs)
        if "cbtype" in kwargs:
            if kwargs["cbtype"] == CallbackType.DATAPREP:
                if "docs" in kwargs:
                    return self.run_data_prepare_cb(self, docs=kwargs["docs"])
            if kwargs["cbtype"] == CallbackType.RETRIEVE:
                if "chat_request" in kwargs:
                    return self.run_retriever_cb(self, chat_request=kwargs["chat_request"])
            if kwargs["cbtype"] == CallbackType.PIPELINE:
                if "chat_request" in kwargs:
                    return self.run_pipeline_cb(self, chat_request=kwargs["chat_request"])

    def update(self, node_parser=None, indexer=None, retriever=None, postprocessor=None, generator=None):
        if node_parser is not None:
            self.node_parser = node_parser
        if indexer is not None:
            self.indexer = indexer
        if retriever is not None:
            self.retriever = retriever
        if postprocessor is not None:
            self.postprocessor = postprocessor
        if generator is not None:
            self.generator = generator

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "name": self.name,
            "comp_type": self.comp_type,
            "node_parser": self.node_parser,
            "indexer": self.indexer,
            "retriever": self.retriever,
            "postprocessor": self.postprocessor,
            "generator": self.generator,
            "status": self.status,
        }
        return set

    def model_existed(self, model_id: str) -> bool:
        # judge if the given model is existed in a pipeline by model_id
        if self.indexer:
            if hasattr(self.indexer, "_embed_model") and self.indexer._embed_model.model_id == model_id:
                return True
            if hasattr(self.indexer, "_llm") and self.indexer._llm.model_id == model_id:
                return True
        if self.postprocessor:
            for processor in self.postprocessor:
                if hasattr(processor, "model_id") and processor.model_id == model_id:
                    return True
        if self.generator:
            llm = self.generator.llm
            if llm() and llm().model_id == model_id:
                return True
        return False


# Test callback to retrieve nodes from query
def run_test_retrieve(pl: Pipeline, chat_request: ChatCompletionRequest) -> Any:
    query = chat_request.messages
    retri_res = pl.retriever.run(query=query)
    query_bundle = QueryBundle(query)
    if pl.postprocessor:
        for processor in pl.postprocessor:
            if (
                isinstance(processor, RerankProcessor)
                and chat_request.top_n != ChatCompletionRequest.model_fields["top_n"].default
            ):
                processor.top_n = chat_request.top_n
            retri_res = processor.run(retri_res=retri_res, query_bundle=query_bundle)
    return retri_res


def run_simple_doc(pl: Pipeline, docs: List[Document]) -> Any:
    n = pl.node_parser.run(docs=docs)
    if pl.indexer is not None:
        pl.indexer.insert_nodes(n)
    print(pl.indexer._index_struct)
    return n


def run_test_generator(pl: Pipeline, chat_request: ChatCompletionRequest) -> Any:
    query = chat_request.messages
    retri_res = pl.retriever.run(query=query)
    query_bundle = QueryBundle(query)
    if pl.postprocessor:
        for processor in pl.postprocessor:
            if (
                isinstance(processor, RerankProcessor)
                and chat_request.top_n != ChatCompletionRequest.model_fields["top_n"].default
            ):
                processor.top_n = chat_request.top_n
            retri_res = processor.run(retri_res=retri_res, query_bundle=query_bundle)
    if pl.generator is None:
        return "No Generator Specified"
    if pl.generator.inference_type == InferenceType.LOCAL:
        answer = pl.generator.run(chat_request, retri_res)
    elif pl.generator.inference_type == InferenceType.VLLM:
        answer = pl.generator.run_vllm(chat_request, retri_res)
    return answer

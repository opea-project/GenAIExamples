# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, List, Optional

from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.base import BaseComponent, CallbackType, CompType, InferenceType, RetrieverType
from edgecraftrag.components.postprocessor import RerankProcessor
from edgecraftrag.components.query_preprocess import query_search
from edgecraftrag.components.retriever import AutoMergeRetriever, SimpleBM25Retriever, VectorSimRetriever
from fastapi.responses import StreamingResponse
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
    benchmark: Optional[BaseComponent] = Field(default=None)
    status: PipelineStatus = Field(default=PipelineStatus())
    run_pipeline_cb: Optional[Callable[..., Any]] = Field(default=None)
    run_retriever_cb: Optional[Callable[..., Any]] = Field(default=None)
    run_data_prepare_cb: Optional[Callable[..., Any]] = Field(default=None)

    def __init__(
        self,
        name,
        origin_json=None,
    ):
        super().__init__(name=name, comp_type=CompType.PIPELINE)
        if self.name == "" or self.name is None:
            self.name = self.idx
        self.enable_benchmark = os.getenv("ENABLE_BENCHMARK", "False").lower() == "true"
        self.run_pipeline_cb = run_generator
        self.run_retriever_cb = run_retrieve
        self.run_data_prepare_cb = run_simple_doc

        self._node_changed = False
        self._index_changed = False
        self._index_to_retriever_updated = True
        self._origin_json = origin_json

    # TODO: consider race condition
    @property
    def get_pipeline_json(self) -> str:
        return self._origin_json

    def update_pipeline_json(self, pipeline_dict):
        origin_json = json.loads(self._origin_json)
        for k, v in pipeline_dict.items():
            if v is not None:
                origin_json[k] = v
        self._origin_json = json.dumps(origin_json)

    @property
    def node_changed(self) -> bool:
        return self._node_changed

    def reset_node_status(self) -> bool:
        self._node_changed = False
        self._index_changed = False
        self._index_to_retriever_updated = True

    def check_active(self, nodelist, kb_name):
        if self._node_changed:
            if not self._index_changed:
                print("Reinitializing indexer ...")
                self.indexer.reinitialize_indexer(kb_name)
                self._index_changed = True
                self._index_to_retriever_updated = False

            if nodelist is not None and len(nodelist) > 0:
                self.update_nodes(nodelist)
            self._node_changed = False

        # Due to limitation, need to update retriever's db after reinitialize_indexer()
        if self._index_changed and not self._index_to_retriever_updated:
            self.update_indexer_to_retriever()
            self._index_changed = False
            self._index_to_retriever_updated = True

        self.reset_node_status()

    # TODO: update doc changes
    # TODO: more operations needed, add, del, modify
    def update_nodes(self, nodes):
        if self.indexer is not None:
            self.indexer.insert_nodes(nodes)

    def update_indexer_to_retriever(self):
        if self.indexer is not None and self.retriever is not None:
            old_retriever = self.retriever
            retriever_type = old_retriever.comp_subtype
            similarity_top_k = old_retriever.topk
            match retriever_type:
                case RetrieverType.VECTORSIMILARITY:
                    new_retriever = VectorSimRetriever(self.indexer, similarity_top_k=similarity_top_k)
                case RetrieverType.AUTOMERGE:
                    new_retriever = AutoMergeRetriever(self.indexer, similarity_top_k=similarity_top_k)
                case RetrieverType.BM25:
                    new_retriever = SimpleBM25Retriever(self.indexer, similarity_top_k=similarity_top_k)
                case _:
                    new_retriever = old_retriever

            self.retriever = new_retriever

    # Implement abstract run function
    # callback dispatcher
    def run(self, **kwargs) -> Any:
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
            if isinstance(llm, str):
                return llm == model_id
            else:
                return llm().model_id == model_id
        return False


# Test callback to retrieve nodes from query
def run_retrieve(pl: Pipeline, chat_request: ChatCompletionRequest) -> Any:
    benchmark_data = {}
    query = chat_request.messages
    top_k = None if chat_request.k == ChatCompletionRequest.model_fields["k"].default else chat_request.k
    contexts = {}
    start = 0
    if pl.enable_benchmark:
        _, benchmark_data = pl.benchmark.init_benchmark_data()
        start = time.perf_counter()
    retri_res = pl.retriever.run(query=query, top_k=top_k)
    if pl.enable_benchmark:
        benchmark_data[CompType.RETRIEVER] = time.perf_counter() - start
        pl.benchmark.insert_benchmark_data(benchmark_data)
    contexts[CompType.RETRIEVER] = retri_res
    query_bundle = QueryBundle(query)
    if pl.postprocessor:
        for processor in pl.postprocessor:
            if (
                isinstance(processor, RerankProcessor)
                and chat_request.top_n != ChatCompletionRequest.model_fields["top_n"].default
            ):
                processor.top_n = chat_request.top_n
            retri_res = processor.run(retri_res=retri_res, query_bundle=query_bundle)
            contexts[CompType.POSTPROCESSOR] = retri_res
    return contexts


def run_simple_doc(pl: Pipeline, docs: List[Document]) -> Any:
    start = 0
    benchmark_data = {}
    if pl.enable_benchmark:
        _, benchmark_data = pl.benchmark.init_benchmark_data()
        start = time.perf_counter()
    n = pl.node_parser.run(docs=docs)
    if pl.indexer is not None:
        pl.indexer.insert_nodes(n)
    if pl.enable_benchmark:
        benchmark_data[CompType.NODEPARSER] += time.perf_counter() - start
        benchmark_data[CompType.CHUNK_NUM] += len(n)
        pl.benchmark.insert_benchmark_data(benchmark_data)
    return n


def benchmark_response(ret, benchmark, benchmark_index, benchmark_data, input_token_size, start):
    if isinstance(ret, StreamingResponse):
        original_body_iterator = ret.body_iterator

        async def timing_wrapper():
            async for chunk in original_body_iterator:
                yield chunk
            benchmark_data[CompType.GENERATOR] = time.perf_counter() - start
            benchmark.insert_llm_data(benchmark_index, input_token_size)
            benchmark.insert_benchmark_data(benchmark_data)

        ret.body_iterator = timing_wrapper()
        return ret
    else:
        return ret


def run_generator(pl: Pipeline, chat_request: ChatCompletionRequest) -> Any:
    if pl.enable_benchmark:
        benchmark_index, benchmark_data = pl.benchmark.init_benchmark_data()
    contexts = {}
    retri_res = []
    active_kb = chat_request.user if chat_request.user else None
    enable_rag_retrieval = (
        chat_request.chat_template_kwargs.get("enable_rag_retrieval", True)
        if chat_request.chat_template_kwargs
        else True
    )
    if not active_kb:
        enable_rag_retrieval = False
    elif pl.retriever.comp_subtype == "kbadmin_retriever" and active_kb.comp_subtype == "origin_kb":
        enable_rag_retrieval = False
    elif pl.retriever.comp_subtype != "kbadmin_retriever" and active_kb.comp_subtype == "kbadmin_kb":
        enable_rag_retrieval = False
    query = chat_request.messages
    sub_questionss_result = None
    experience_status = True if chat_request.tool_choice == "auto" else False
    if enable_rag_retrieval:
        start = 0
        if pl.enable_benchmark:
            start = time.perf_counter()
        if pl.generator.inference_type == InferenceType.VLLM and experience_status:
            UI_DIRECTORY = "/home/user/ui_cache"
            search_config_path = os.path.join(UI_DIRECTORY, "configs/search_config.yaml")
            search_dir = os.path.join(UI_DIRECTORY, "configs/experience_dir/experience.json")

            def run_async_query_search():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(query_search(query, search_config_path, search_dir, pl))
                finally:
                    loop.close()

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_async_query_search)
                top1_issue, sub_questionss_result = future.result()
            if sub_questionss_result:
                query = query + sub_questionss_result
        if pl.enable_benchmark:
            benchmark_data[CompType.QUERYSEARCH] = time.perf_counter() - start
            start = time.perf_counter()
        top_k = None if chat_request.k == ChatCompletionRequest.model_fields["k"].default else chat_request.k
        retri_res = pl.retriever.run(query=query, top_k=top_k)
        if pl.enable_benchmark:
            benchmark_data[CompType.RETRIEVER] = time.perf_counter() - start
        contexts[CompType.RETRIEVER] = retri_res
        query_bundle = QueryBundle(query)
        if pl.enable_benchmark:
            start = time.perf_counter()
        if pl.postprocessor:
            for processor in pl.postprocessor:
                if (
                    isinstance(processor, RerankProcessor)
                    and chat_request.top_n != ChatCompletionRequest.model_fields["top_n"].default
                ):
                    processor.top_n = chat_request.top_n
                retri_res = processor.run(retri_res=retri_res, query_bundle=query_bundle)
                contexts[CompType.POSTPROCESSOR] = retri_res
        if pl.enable_benchmark:
            benchmark_data[CompType.POSTPROCESSOR] = time.perf_counter() - start

    if pl.generator is None:
        raise ValueError("No Generator Specified")

    if pl.enable_benchmark:
        _, prompt_str = pl.generator.query_transform(chat_request, retri_res)
        input_token_size = pl.benchmark.cal_input_token_size(prompt_str)

    np_type = pl.node_parser.comp_subtype
    if pl.enable_benchmark:
        start = time.perf_counter()
    if pl.generator.inference_type == InferenceType.LOCAL:
        ret = pl.generator.run(chat_request, retri_res, np_type)
    elif pl.generator.inference_type == InferenceType.VLLM:
        ret = pl.generator.run_vllm(chat_request, retri_res, np_type, sub_questions=sub_questionss_result)
    else:
        raise ValueError("LLM inference_type not supported")
    if pl.enable_benchmark:
        end = time.perf_counter()
        if isinstance(ret, StreamingResponse):
            ret = benchmark_response(ret, pl.benchmark, benchmark_index, benchmark_data, input_token_size, start)
        else:
            benchmark_data[CompType.GENERATOR] = end - start
            pl.benchmark.insert_llm_data(benchmark_index, input_token_size)
            pl.benchmark.insert_benchmark_data(benchmark_data)
    return ret, contexts

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, List, Optional

from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.base import (
    BaseComponent,
    CallbackType,
    CompType,
    GeneratorType,
    InferenceType,
    RetrieverType,
)
from edgecraftrag.base import NodeParserType
from edgecraftrag.components.generator import clone_generator
from edgecraftrag.components.postprocessor import RerankProcessor
from edgecraftrag.components.query_preprocess import query_search
from edgecraftrag.components.retriever import AutoMergeRetriever, SimpleBM25Retriever, VectorSimRetriever, KBadminRetriever
from edgecraftrag.env import SEARCH_CONFIG_PATH, SEARCH_DIR
from fastapi.responses import StreamingResponse
from llama_index.core.schema import QueryBundle
from pydantic import BaseModel, Field, model_serializer


class PipelineStatus(BaseModel):
    active: bool = False


class Pipeline(BaseComponent):

    retrievers: Optional[List[BaseComponent]] = Field(default=None)
    postprocessor: Optional[List[BaseComponent]] = Field(default=None)
    generator: Optional[List[BaseComponent]] = Field(default=None)
    benchmark: Optional[BaseComponent] = Field(default=None)
    status: PipelineStatus = Field(default=PipelineStatus())
    run_pipeline_cb: Optional[Callable[..., Any]] = Field(default=None)
    run_retriever_postprocessor_cb: Optional[Callable[..., Any]] = Field(default=None)
    run_retriever_cb: Optional[Callable[..., Any]] = Field(default=None)
    run_postprocessor_cb: Optional[Callable[..., Any]] = Field(default=None)
    run_query_search_cb: Optional[Callable[..., Any]] = Field(default=None)

    def __init__(
        self,
        name,
        origin_json=None,
        idx=None,
    ):
        super().__init__(name=name, comp_type=CompType.PIPELINE)
        if self.name == "" or self.name is None:
            self.name = self.idx
        if idx is not None:
            self.idx = str(idx)

        self.enable_benchmark = os.getenv("ENABLE_BENCHMARK", "False").lower() == "true"
        self.run_pipeline_cb = run_pipeline
        self.run_retriever_postprocessor_cb = run_retrieve_postprocess
        self.run_retriever_cb = run_retrieve
        self.run_postprocessor_cb = run_postprocess
        self.run_generator_cb = run_generator
        self.run_query_search_cb = run_query_search
        self._origin_json = origin_json if origin_json is not None else "{}"
        self.retriever_type = ""
        self.retrieve_topk = 0
        self.retrievers = []

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

    # Implement abstract run function
    # callback dispatcher
    async def run(self, **kwargs) -> Any:
        if "cbtype" in kwargs:
            if kwargs["cbtype"] == CallbackType.RETRIEVE_POSTPROCESS:
                if "chat_request" in kwargs:
                    return await self.run_retriever_postprocessor_cb(self, chat_request=kwargs["chat_request"])
            if kwargs["cbtype"] == CallbackType.RETRIEVE:
                if "chat_request" in kwargs:
                    return await self.run_retriever_cb(self, chat_request=kwargs["chat_request"])
            if kwargs["cbtype"] == CallbackType.POSTPROCESS:
                if "chat_request" in kwargs and "contexts" in kwargs:
                    return await self.run_postprocessor_cb(
                        self, chat_request=kwargs["chat_request"], contexts=kwargs["contexts"]
                    )
            if kwargs["cbtype"] == CallbackType.GENERATE:
                if "chat_request" in kwargs:
                    generator_type = kwargs.get("generator_type", GeneratorType.CHATQNA)
                    return await self.run_generator_cb(
                        self, chat_request=kwargs["chat_request"], generator_type=generator_type
                    )
            if kwargs["cbtype"] == CallbackType.PIPELINE:
                if "chat_request" in kwargs:
                    generator_type = kwargs.get("generator_type", GeneratorType.CHATQNA)
                    return await self.run_pipeline_cb(
                        self, chat_request=kwargs["chat_request"], generator_type=generator_type
                    )
            if kwargs["cbtype"] == CallbackType.QUERYSEARCH:
                if "chat_request" in kwargs:
                    return await self.run_query_search_cb(self, chat_request=kwargs["chat_request"])

    def update(self, retrievers=None, postprocessor=None, generator=None):
        if retrievers is not None:
            self.retrievers = retrievers
        if postprocessor is not None:
            self.postprocessor = postprocessor
        if generator is not None:
            self.generator = generator

    @model_serializer
    def ser_model(self):
        retriever_config = self.retrievers[0] if self.retrievers else None
        set = {
            "idx": self.idx,
            "name": self.name,
            "comp_type": self.comp_type,
            "retriever": retriever_config,
            "postprocessor": self.postprocessor,
            "generator": self.generator,
            "status": self.status,
        }
        return set

    def model_existed(self, model_id: str) -> bool:
        # judge if the given model is existed in a pipeline by model_id
        if self.postprocessor:
            for processor in self.postprocessor:
                if hasattr(processor, "model_id") and processor.model_id == model_id:
                    return True
        if self.generator:
            for generator in self.generator:
                llm = generator.llm
                if isinstance(llm, str):
                    return llm == model_id
                else:
                    return llm().model_id == model_id
        return False

    def get_generator(self, generator_type: str) -> Optional[BaseComponent]:
        if self.generator:
            for gen in self.generator:
                if gen.comp_subtype == generator_type:
                    return gen
        return None
    def update_retriever_config(self, retriever_type: str, retrieve_topk: int):
        self.retriever_type = retriever_type
        self.retrieve_topk = retrieve_topk

    def update_retriever_list(self, active_kbs):
        self.clear_retrievers()
        for active_kb in active_kbs:
            indexer = active_kb.indexer
            if indexer is not None:
                similarity_top_k = self.retrieve_topk
                retriever = None
                if active_kb.comp_subtype == "kbadmin_kb":
                    # For kbadmin_kb, only KBadminRetriever is supported
                    retriever = KBadminRetriever(indexer, similarity_top_k=similarity_top_k)
                else:
                    match self.retriever_type:
                        case RetrieverType.VECTORSIMILARITY:
                            retriever = VectorSimRetriever(indexer, similarity_top_k=similarity_top_k)
                        case RetrieverType.AUTOMERGE:
                            retriever = AutoMergeRetriever(indexer, similarity_top_k=similarity_top_k)
                        case RetrieverType.BM25:
                            retriever = SimpleBM25Retriever(indexer, similarity_top_k=similarity_top_k)
                        case _:
                            raise ValueError(f"Retriever type {self.retriever_type} not supported")
                if retriever:
                    self.retrievers.append(retriever)

    def update_retriever(self, kb, prev_indexer):
        indexer = kb.indexer
        for i, retriever in enumerate(self.retrievers):
            if prev_indexer == retriever._index:
                similarity_top_k = self.retrieve_topk
                if kb.comp_subtype == "kbadmin_kb":
                    # For kbadmin_kb, only KBadminRetriever is supported
                    retriever = KBadminRetriever(indexer, similarity_top_k=similarity_top_k)
                else:
                    match self.retriever_type:
                        case RetrieverType.VECTORSIMILARITY:
                            retriever = VectorSimRetriever(indexer, similarity_top_k=similarity_top_k)
                        case RetrieverType.AUTOMERGE:
                            retriever = AutoMergeRetriever(indexer, similarity_top_k=similarity_top_k)
                        case RetrieverType.BM25:
                            retriever = SimpleBM25Retriever(indexer, similarity_top_k=similarity_top_k)
                        case _:
                            raise ValueError(f"Retriever type {self.retriever_type} not supported")
                break

    
    def clear_retrievers(self):
        self.retrievers = []

    def create_freechat_gen_from_chatqna_gen(self) -> bool:
        if len(self.generator) == 0 or self.generator[0].comp_subtype != GeneratorType.CHATQNA:
            return False

        dst_generator_cfg = {"generator_type": GeneratorType.FREECHAT}
        new_gen = clone_generator(self.generator[0], dst_generator_cfg)
        if new_gen:
            self.generator.append(new_gen)
            # update pipeline json
            origin_json = json.loads(self._origin_json)
            new_gen_config = origin_json["generator"][0].copy()
            new_gen_config["generator_type"] = GeneratorType.FREECHAT
            new_gen_config.pop("prompt_path", None)
            new_gen_config.pop("prompt_content", None)
            origin_json["generator"].append(new_gen_config)
            self._origin_json = json.dumps(origin_json)
            return True
        return False


async def run_retrieve(pl: Pipeline, chat_request: ChatCompletionRequest) -> Any:
    query = chat_request.messages
    top_k = None if chat_request.k == ChatCompletionRequest.model_fields["k"].default else chat_request.k
    contexts = {}
    start = 0
    if pl.enable_benchmark:
        benchmark_index = pl.benchmark.init_benchmark_data()
        start = time.perf_counter()
    retri_res = []
    for retriever in pl.retrievers:
        retri_res.extend(retriever.run(query=query, top_k=top_k))
    if pl.enable_benchmark:
        pl.benchmark.update_benchmark_data(benchmark_index, CompType.RETRIEVER, time.perf_counter() - start)
    contexts[CompType.RETRIEVER] = retri_res
    return contexts


async def run_postprocess(pl: Pipeline, chat_request: ChatCompletionRequest, contexts) -> Any:
    if CompType.RETRIEVER not in contexts:
        raise ValueError("No retrieved contexts identified.")
    query = chat_request.messages
    query_bundle = QueryBundle(query)
    if pl.postprocessor:
        # TODO: Consider multiple postprocessors
        for processor in pl.postprocessor:
            if (
                isinstance(processor, RerankProcessor)
                and chat_request.top_n != ChatCompletionRequest.model_fields["top_n"].default
            ):
                processor.top_n = chat_request.top_n
            retri_res = processor.run(retri_res=contexts.get(CompType.RETRIEVER), query_bundle=query_bundle)
            contexts[CompType.POSTPROCESSOR] = retri_res
    return contexts


# Test callback to retrieve and rerank nodes from query
async def run_retrieve_postprocess(pl: Pipeline, chat_request: ChatCompletionRequest) -> Any:
    query = chat_request.messages
    top_k = None if chat_request.k == ChatCompletionRequest.model_fields["k"].default else chat_request.k
    contexts = {}
    start = 0
    if pl.enable_benchmark:
        benchmark_index = pl.benchmark.init_benchmark_data()
        start = time.perf_counter()
    retri_res = []
    for retriever in pl.retrievers:
        retri_res.extend(retriever.run(query=query, top_k=top_k))
    if pl.enable_benchmark:
        pl.benchmark.update_benchmark_data(benchmark_index, CompType.RETRIEVER, time.perf_counter() - start)
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


async def run_query_search(pl: Pipeline, chat_request: ChatCompletionRequest) -> Any:
    query = chat_request.messages

    def run_async_query_search():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(query_search(query, SEARCH_CONFIG_PATH, SEARCH_DIR, pl))
        finally:
            loop.close()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_async_query_search)
        top1_issue, sub_questionss_result = future.result()
    if sub_questionss_result:
        query = query + sub_questionss_result
    return query, sub_questionss_result


async def run_pipeline(
    pl: Pipeline, chat_request: ChatCompletionRequest, generator_type: str = GeneratorType.CHATQNA
) -> Any:
    benchmark_index = -1
    if pl.enable_benchmark:
        benchmark_index = pl.benchmark.init_benchmark_data()
    contexts = {}
    retri_res = []
    active_kbs = chat_request.user if chat_request.user else []
    enable_rag_retrieval = (
        chat_request.chat_template_kwargs.get("enable_rag_retrieval", True)
        if chat_request.chat_template_kwargs
        else True
    )
    if not active_kbs:
        enable_rag_retrieval = False
    # If using multiple knowledge bases, unstructured node parser cannot work with other types of node parser
    np_types = set()
    for kb in active_kbs:
        if kb.comp_subtype == "kbadmin_kb":
            np_types.add("kbadmin_node_parser")
        else:
            np_types.add(kb.node_parser.comp_subtype)
    if len(np_types) > 1 and NodeParserType.UNSTRUCTURED in np_types:
        raise ValueError("unstructured node parser cannot work with other types of node parser")
    np_type = next(iter(np_types), None)
    query = chat_request.messages
    sub_questionss_result = None
    experience_status = True if chat_request.tool_choice == "auto" else False
    target_generator = pl.get_generator(generator_type)
    if target_generator is None:
        raise ValueError(f"No Generator ({generator_type}) Specified")
    if enable_rag_retrieval:
        start = 0
        if pl.enable_benchmark:
            start = time.perf_counter()
        if target_generator.inference_type == InferenceType.VLLM and experience_status:
            query, sub_questionss_result = await run_query_search(pl, chat_request)
        if pl.enable_benchmark:
            pl.benchmark.update_benchmark_data(benchmark_index, CompType.QUERYSEARCH, time.perf_counter() - start)
            start = time.perf_counter()
        top_k = (
            None
            if chat_request.k == pl.retrievers[0].topk or chat_request.k != 0 or chat_request.k is None
            else chat_request.k
        )
        retri_res = []
        for retriever in pl.retrievers:
            retri_res.extend(retriever.run(query=query, top_k=top_k))
        if pl.enable_benchmark:
            pl.benchmark.update_benchmark_data(benchmark_index, CompType.RETRIEVER, time.perf_counter() - start)
            start = time.perf_counter()
        contexts[CompType.RETRIEVER] = retri_res
        query_bundle = QueryBundle(query)
        if pl.postprocessor:
            for processor in pl.postprocessor:
                if (
                    isinstance(processor, RerankProcessor)
                    and chat_request.top_n != processor.top_n
                    and chat_request.top_n != 0
                    and chat_request.top_n is not None
                    and chat_request.top_n != ChatCompletionRequest.model_fields["top_n"].default
                ):
                    processor.top_n = chat_request.top_n
                retri_res = processor.run(retri_res=retri_res, query_bundle=query_bundle)
                contexts[CompType.POSTPROCESSOR] = retri_res
        if pl.enable_benchmark:
            pl.benchmark.update_benchmark_data(benchmark_index, CompType.POSTPROCESSOR, time.perf_counter() - start)

    if pl.enable_benchmark:
        _, prompt_str = target_generator.query_transform(chat_request, retri_res)
        input_token_size = pl.benchmark.cal_input_token_size(prompt_str)

    if pl.enable_benchmark:
        start = time.perf_counter()
    if target_generator.inference_type == InferenceType.LOCAL:
        ret = await target_generator.run(chat_request, retri_res, np_type)
    elif target_generator.inference_type == InferenceType.VLLM:
        ret = await target_generator.run_vllm(
            chat_request,
            retri_res,
            np_type,
            sub_questions=sub_questionss_result,
            benchmark=pl.benchmark,
            benchmark_index=benchmark_index,
        )
    else:
        raise ValueError("LLM inference_type not supported")
    if not isinstance(ret, StreamingResponse) and pl.enable_benchmark:
        pl.benchmark.update_benchmark_data(benchmark_index, CompType.GENERATOR, time.perf_counter() - start)
        pl.benchmark.insert_llm_data(benchmark_index, input_token_size)
    return ret, contexts


async def run_generator(
    pl: Pipeline, chat_request: ChatCompletionRequest, generator_type: str = GeneratorType.CHATQNA
) -> Any:
    active_kbs = chat_request.user if chat_request.user else []
     # If using multiple knowledge bases, unstructured node parser cannot work with other types of node parser
    np_types = {kb.node_parser.comp_subtype for kb in active_kbs}
    if len(np_types) > 1 and NodeParserType.UNSTRUCTURED in np_types:
        raise ValueError("unstructured node parser cannot work with other types of node parser")
    np_type = active_kbs[0].node_parser.comp_subtype if active_kbs else None
    target_generator = pl.get_generator(generator_type)
    if target_generator is None:
        raise ValueError(f"No Generator ({generator_type}) Specified")
    if target_generator.inference_type == InferenceType.LOCAL:
        ret = await target_generator.run(chat_request, [], np_type)
    elif target_generator.inference_type == InferenceType.VLLM:
        ret = await target_generator.run_vllm(chat_request, [], np_type)
    else:
        raise ValueError("LLM inference_type not supported")
    return ret

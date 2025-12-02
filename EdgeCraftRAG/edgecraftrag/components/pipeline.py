# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, List, Optional

from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.base import BaseComponent, CallbackType, CompType, InferenceType, NodeParserType, RetrieverType
from edgecraftrag.components.postprocessor import RerankProcessor
from edgecraftrag.components.query_preprocess import query_search
from edgecraftrag.components.retriever import AutoMergeRetriever, SimpleBM25Retriever, VectorSimRetriever
from edgecraftrag.env import SEARCH_CONFIG_PATH, SEARCH_DIR
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
    run_retriever_postprocessor_cb: Optional[Callable[..., Any]] = Field(default=None)
    run_retriever_cb: Optional[Callable[..., Any]] = Field(default=None)
    run_postprocessor_cb: Optional[Callable[..., Any]] = Field(default=None)
    run_data_prepare_cb: Optional[Callable[..., Any]] = Field(default=None)
    run_query_search_cb: Optional[Callable[..., Any]] = Field(default=None)

    def __init__(
        self,
        name,
        origin_json=None,
        idx=None,
        documents_cache=None,
    ):
        super().__init__(name=name, comp_type=CompType.PIPELINE)
        if self.name == "" or self.name is None:
            self.name = self.idx
        if idx is not None:
            self.idx = str(idx)
        if documents_cache is not None:
            self.documents_cache = documents_cache
        else:
            self.documents_cache = {}

        self.enable_benchmark = os.getenv("ENABLE_BENCHMARK", "False").lower() == "true"
        self.run_pipeline_cb = run_pipeline
        self.run_retriever_postprocessor_cb = run_retrieve_postprocess
        self.run_retriever_cb = run_retrieve
        self.run_postprocessor_cb = run_postprocess
        self.run_generator_cb = run_generator
        self.run_data_prepare_cb = run_simple_doc
        self.run_query_search_cb = run_query_search
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
    async def run(self, **kwargs) -> Any:
        if "cbtype" in kwargs:
            if kwargs["cbtype"] == CallbackType.DATAPREP:
                if "docs" in kwargs:
                    return await self.run_data_prepare_cb(self, docs=kwargs["docs"])
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
                    return await self.run_generator_cb(self, chat_request=kwargs["chat_request"])
            if kwargs["cbtype"] == CallbackType.PIPELINE:
                if "chat_request" in kwargs:
                    return await self.run_pipeline_cb(self, chat_request=kwargs["chat_request"])
            if kwargs["cbtype"] == CallbackType.QUERYSEARCH:
                if "chat_request" in kwargs:
                    return await self.run_query_search_cb(self, chat_request=kwargs["chat_request"])

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

    def add_docs_to_list(self, kb_name, file_paths):
        if self.indexer.comp_subtype != "milvus_vector":
            return None
        target_config = self.connect_target_config()
        if kb_name not in self.documents_cache:
            self.documents_cache[kb_name] = {"files": [], "config": target_config}
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        self.documents_cache[kb_name]["files"].extend(file_paths)

    def del_docs_to_list(self, kb_name, file_paths):
        if kb_name not in self.documents_cache:
            return None
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        for file_path in file_paths:
            if file_path in self.documents_cache[kb_name]["files"]:
                self.documents_cache[kb_name]["files"].remove(file_path)

    def clear_document_cache(self, kb_name):
        if kb_name in self.documents_cache:
            del self.documents_cache[kb_name]

    def compare_file_lists(self, kb_name, current_files):
        self.add_docs_to_list(kb_name, [])
        target_config = self.connect_target_config()
        if self.documents_cache[kb_name]["config"] == target_config:
            diff = self.compare_mappings(self.documents_cache[kb_name]["files"], current_files)
        else:
            self.documents_cache[kb_name] = {"files": [], "config": self.connect_target_config()}
            diff = {"add_docs": current_files}
        return diff

    def compare_mappings(self, stored_files, new_files):
        stored = set(stored_files)
        new = set(new_files)
        return {"add_docs": list(new - stored), "del_docs": list(stored - new)}

    def connect_target_config(self):
        target_config = ""
        if self.node_parser.comp_subtype == NodeParserType.SIMPLE:
            target_config = (
                "simple"
                + str(self.node_parser.chunk_size)
                + str(self.node_parser.chunk_overlap)
                + self.indexer.model.model_id
            )
        elif self.node_parser.comp_subtype == NodeParserType.SENTENCEWINDOW:
            target_config = "sentencewindow" + str(self.node_parser.window_size) + self.indexer.model.model_id
        elif self.node_parser.comp_subtype == NodeParserType.HIERARCHY:
            target_config = "hierarchical" + self.indexer.model.model_id
        elif self.node_parser.comp_subtype == NodeParserType.UNSTRUCTURED:
            target_config = (
                "target_config"
                + str(self.node_parser.chunk_size)
                + str(self.node_parser.chunk_overlap)
                + self.indexer.model.model_id
            )
        return target_config

    def nodes_to_document(self, node_dict: dict):
        nodes = []
        for node_info in node_dict.values():
            nodes.append({"start": int(node_info["start_char_idx"]), "text": node_info["text"]})
        nodes_sorted = sorted(nodes, key=lambda x: x["start"])
        if not nodes_sorted:
            return ""
        merged_text = nodes_sorted[0]["text"]
        for i in range(1, len(nodes_sorted)):
            prev_text = merged_text
            curr_text = nodes_sorted[i]["text"]
            max_possible_overlap = min(len(prev_text), len(curr_text))
            overlap_len = 0
            for j in range(max_possible_overlap, 0, -1):
                if prev_text.endswith(curr_text[:j]):
                    overlap_len = j
                    break
            merged_text += curr_text[overlap_len:]
        return merged_text

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


async def run_retrieve(pl: Pipeline, chat_request: ChatCompletionRequest) -> Any:
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


async def run_simple_doc(pl: Pipeline, docs: List[Document]) -> Any:
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


async def run_pipeline(pl: Pipeline, chat_request: ChatCompletionRequest) -> Any:
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
            query, sub_questionss_result = await run_query_search(pl, chat_request)
        if pl.enable_benchmark:
            benchmark_data[CompType.QUERYSEARCH] = time.perf_counter() - start
            start = time.perf_counter()
        top_k = (
            None
            if chat_request.k == pl.retriever.topk or chat_request.k != 0 or chat_request.k is None
            else chat_request.k
        )
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
                    and chat_request.top_n != processor.top_n
                    and chat_request.top_n != 0
                    and chat_request.top_n is not None
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
        ret = await pl.generator.run(chat_request, retri_res, np_type)
    elif pl.generator.inference_type == InferenceType.VLLM:
        ret = await pl.generator.run_vllm(chat_request, retri_res, np_type, sub_questions=sub_questionss_result)
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


async def run_generator(pl: Pipeline, chat_request: ChatCompletionRequest) -> Any:
    np_type = pl.node_parser.comp_subtype
    if pl.generator.inference_type == InferenceType.LOCAL:
        ret = await pl.generator.run(chat_request, [], np_type)
    elif pl.generator.inference_type == InferenceType.VLLM:
        ret = await pl.generator.run_vllm(chat_request, [], np_type)
    else:
        raise ValueError("LLM inference_type not supported")
    return ret

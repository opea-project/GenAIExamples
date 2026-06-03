# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import os
import time
import gc
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, List, Optional
from openvino import Core
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
from edgecraftrag.components.knowledge_base import Knowledge
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
        self.max_util = round((
            0.95 - float(os.environ.get("GPU_MEMORY_UTIL", 0))
            if "LLM_MODEL" in os.environ
            else 0.95
        ),3)
        self.run_pipeline_cb = run_pipeline
        self.run_retriever_postprocessor_cb = run_retrieve_postprocess
        self.run_retriever_cb = run_retrieve
        self.run_postprocessor_cb = run_postprocess
        self.run_generator_cb = run_generator
        self.run_query_search_cb = run_query_search
        self._origin_json = origin_json if origin_json is not None else "{}"
        self.retriever_type = ""
        self.retrieve_topk = 0
        self.max_retrieve_topk=0
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

    def _update_config_and_retrievers(self, changed: bool) -> None:
        """Helper method to update JSON config and retriever settings."""
        origin_json = json.loads(self._origin_json)
        origin_json["retriever"]["retrieve_topk"] = self.retrieve_topk
        origin_json["retriever"]["max_retrieve_topk"] = self.max_retrieve_topk
        
        for retriever in self.retrievers:
            retriever.topk = self.retrieve_topk
        
        if self.postprocessor:
            for i, processor in enumerate(self.postprocessor):
                processor.top_n = min(processor.top_n, self.max_retrieve_topk)
                origin_json["postprocessor"][i]["top_n"] = processor.top_n
        
        self._origin_json = json.dumps(origin_json)

    def _resolve_max_util(self, reranker_device: str, core: Core) -> float:
        """Resolve memory utilization rate based on device and inference type."""

        if self.generator[0].inference_type == InferenceType.LOCAL:
            if self.generator[0].llm().device == reranker_device:
                return 0.5
            else:
                return 0.95
        
        if reranker_device == "CPU" or reranker_device == "NPU":
            return 0.95
        
        device_type_obj = self._safe_get_property(reranker_device, "DEVICE_TYPE", core)
        reranker_card = 0
        if reranker_device == "CPU":
            reranker_device_type = "CPU"
        elif reranker_device == "NPU":
            reranker_device_type = "NPU"
        elif getattr(device_type_obj, "name", "") == "INTEGRATED":
            reranker_device_type = "iGPU"
        else:
            reranker_device_type = "dGPU"
            reranker_card = int(reranker_device.split(".")[1]) - 1

        dgpu_number = 0
        for d in core.available_devices:
            if d.startswith("GPU") and getattr(self._safe_get_property(d, "DEVICE_TYPE", core), "name", "") == "DISCRETE":
                dgpu_number += 1
        mask = os.getenv("VLLM_AFFINITY_MASK", "")
        allowed = set(int(x) for x in mask.split(",") if x.strip().isdigit())
        max_gpu = max(allowed) if allowed else None
       
        if max_gpu >= dgpu_number and int(os.getenv("TP", 1)) > 1:
            vllm_device_type = "iGPU"
        else:
            vllm_device_type = "dGPU"
        if vllm_device_type == "iGPU" and reranker_device_type == "iGPU":
            return self.max_util
        
        if vllm_device_type == "dGPU" and reranker_device_type == "dGPU":
            if reranker_card in allowed:
                return self.max_util
        return 0.95

    def _parse_vllm_device_mask(self) -> Optional[int]:
        """Parse VLLM device affinity mask and return device index."""
        ze_mask = os.environ.get("VLLM_AFFINITY_MASK", "")
        devices = ze_mask.split(",") if ze_mask else []
        if devices and devices[0]:
            try:
                return int(devices[0])
            except (ValueError, IndexError):
                pass
        return None

    @staticmethod
    def _safe_get_property(device_name: str, property_name: str, core: Core):
        """Safely retrieve OpenVINO device property."""
        try:
            return core.get_property(device_name, property_name)
        except Exception:
            return None

    def _calculate_max_retrieve_topk(
        self, available_memory_mb: float, hidden_size: Optional[int], num_hidden_layers: Optional[int], embedding_length: int
    ) -> int:
        """Calculate maximum top-k based on available memory and model config."""
        # Constants for calculation
        MEMORY_CALC_DIVISORS = 2 * 2 * 0.2  # From original formula
        
        if not hidden_size or not num_hidden_layers or embedding_length <= 0:
            return self.retrieve_topk
        
        denominator = hidden_size * num_hidden_layers * MEMORY_CALC_DIVISORS * embedding_length
        max_topk = int(available_memory_mb * 1024 * 1024 / denominator)
        return max(1, max_topk)  # Ensure at least 1

    def _get_reranker_config(self) -> dict:
        """Safely retrieve reranker model configuration."""
        if not self.postprocessor:
            return {}
        
        try:
            model = self.postprocessor[0].model
            if hasattr(model, "_model") and hasattr(model._model, "config"):
                return model._model.config
            return {}
        except Exception:
            return {}

    def check_top_k(self, active_kbs: list[Knowledge]):
        """Limit top_k based on available GPU memory and model configuration."""
        # Initialize device and core
        reranker_model = self.postprocessor[0].model if self.postprocessor else None
        reranker_device = reranker_model.device if reranker_model else "CPU"
        core = Core()

        # Only knowledge KBs with initialized indexer/model participate in top-k memory estimation.
        valid_kbs = []
        for kb in active_kbs or []:
            if getattr(kb, "comp_type", None) != "knowledge":
                continue
            indexer = getattr(kb, "indexer", None)
            model = getattr(indexer, "model", None) if indexer is not None else None
            if indexer is None or model is None:
                continue
            valid_kbs.append(kb)

        # Resolve memory utilization rate
        max_util = self._resolve_max_util(reranker_device, core)
        # Calculate model and memory sizes
        reranker_size = reranker_model.size_mb if reranker_model else 0
        embedding_size = sum(getattr(kb.indexer.model, "size_mb", 0) for kb in valid_kbs)
        embedding_length = max((getattr(kb.indexer, "d", 0) for kb in valid_kbs), default=0)
        
        # Apply default minimums
        embedding_size = embedding_size or 512
        embedding_length = embedding_length or 256

        # Try to get GPU max allocation memory
        gpu_max_alloc_mem_size = self._safe_get_property(reranker_device, "GPU_DEVICE_MAX_ALLOC_MEM_SIZE", core)
        if gpu_max_alloc_mem_size is None:
            # Fallback: keep current top-k if device property not available
            self.max_retrieve_topk = self.retrieve_topk
            self._update_config_and_retrievers(False)
            return False

        # Calculate available GPU memory
        available_memory_mb = gpu_max_alloc_mem_size / 1024 / 1024 * max_util - reranker_size - embedding_size
        # Get model configuration and calculate max top-k
        config = self._get_reranker_config()
        if not isinstance(config, dict) :
            if not hasattr(config, "to_dict"):
                config = {}
            else:
                config = config.to_dict()
        
        num_hidden_layers = config.get("num_hidden_layers") if isinstance(config, dict) else getattr(config, "num_hidden_layers", None)
        hidden_size = (config.get("hidden_size") or config.get("hidden_dim")) if isinstance(config, dict) else (getattr(config, "hidden_size", None) or getattr(config, "hidden_dim", None))
        self.max_retrieve_topk = self._calculate_max_retrieve_topk(
            available_memory_mb, hidden_size, num_hidden_layers, embedding_length
        )

        # Determine if top-k changed and update accordingly
        new_retrieve_topk = min(self.retrieve_topk, self.max_retrieve_topk)
        changed = new_retrieve_topk != self.retrieve_topk
        if changed:
            self.retrieve_topk = new_retrieve_topk

        # Update configuration and return flag
        self._update_config_and_retrievers(changed)
        return changed

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
                and chat_request.top_n is not None
                and chat_request.top_n != 0
                and chat_request.top_n != ChatCompletionRequest.model_fields["top_n"].default
            ):
                processor.top_n = chat_request.top_n
            elif isinstance(processor, RerankProcessor) and chat_request.top_n == 0:
                processor.top_n = processor.default_top_n
            post_res = processor.run(retri_res=contexts.get(CompType.RETRIEVER), query_bundle=query_bundle)
            contexts[CompType.POSTPROCESSOR] = post_res
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
    post_res = []
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
                and chat_request.top_n is not None
                and chat_request.top_n != 0
                and chat_request.top_n != ChatCompletionRequest.model_fields["top_n"].default
            ):
                processor.top_n = chat_request.top_n
            elif isinstance(processor, RerankProcessor) and chat_request.top_n == 0:
                processor.top_n = processor.default_top_n
            post_res = processor.run(retri_res=retri_res, query_bundle=query_bundle)
            contexts[CompType.POSTPROCESSOR] = post_res
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


def cleanup_pipeline_resources(*resources) -> None:
    for resource in resources:
        if hasattr(resource, "clear"):
            resource.clear()
        del resource
    gc.collect()


async def run_pipeline(
    pl: Pipeline, chat_request: ChatCompletionRequest, generator_type: str = GeneratorType.CHATQNA
) -> Any:
    benchmark_index = -1
    if pl.enable_benchmark:
        benchmark_index = pl.benchmark.init_benchmark_data()
    contexts = {}
    retri_res = []
    post_res = []
    top_k = None
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
    query_bundle = None
    sub_questionss_result = None
    experience_status = True if chat_request.tool_choice == "auto" else False
    target_generator = pl.get_generator(generator_type)
    if target_generator is None:
        raise ValueError(f"No Generator ({generator_type}) Specified")
    if enable_rag_retrieval:
        start = 0
        if pl.enable_benchmark:
            start = time.perf_counter()
        if target_generator.inference_type in (InferenceType.VLLM, InferenceType.OVMS) and experience_status:
            query, sub_questionss_result = await run_query_search(pl, chat_request)
        if pl.enable_benchmark:
            pl.benchmark.update_benchmark_data(benchmark_index, CompType.QUERYSEARCH, time.perf_counter() - start)
            start = time.perf_counter()
        top_k = (
            None
            if chat_request.k == pl.retrievers[0].topk or chat_request.k == 0 or chat_request.k is None
            else min(chat_request.k, pl.retrieve_topk)
        )
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
                    processor.top_n = min(chat_request.top_n, top_k) if top_k is not None else chat_request.top_n
                elif isinstance(processor, RerankProcessor) and chat_request.top_n == 0:
                    processor.top_n = processor.default_top_n
                post_res = processor.run(retri_res=retri_res, query_bundle=query_bundle)
                contexts[CompType.POSTPROCESSOR] = post_res
        if pl.enable_benchmark:
            pl.benchmark.update_benchmark_data(benchmark_index, CompType.POSTPROCESSOR, time.perf_counter() - start)

    if pl.enable_benchmark:
        _, prompt_str = target_generator.query_transform(chat_request, post_res)
        input_token_size = pl.benchmark.cal_input_token_size(prompt_str)

    if pl.enable_benchmark:
        start = time.perf_counter()
    if target_generator.inference_type == InferenceType.LOCAL:
        ret = await target_generator.run(chat_request, retri_res, np_type, enable_benchmark=pl.enable_benchmark, benchmark=pl.benchmark, benchmark_index=benchmark_index)
    elif target_generator.inference_type in (InferenceType.VLLM, InferenceType.OVMS):
        ret = await target_generator.run_remote(
            chat_request,
            post_res,
            np_type,
            sub_questions=sub_questionss_result,
            benchmark=pl.benchmark,
            benchmark_index=benchmark_index,
        )
    else:
        raise ValueError("LLM inference_type not supported")
    if not isinstance(ret, StreamingResponse) and pl.enable_benchmark:
        if ( target_generator.inference_type == InferenceType.LOCAL ):
            if ( not chat_request.stream ): 
                pl.benchmark.update_benchmark_data_genai(benchmark_index, CompType.GENERATOR, time.perf_counter() - start, pl.generator[0].llm)
                pl.benchmark.insert_llm_data_genai(benchmark_index, input_token_size, pl.generator[0].llm)
            cleanup_pipeline_resources(retri_res, post_res, np_types, sub_questionss_result)
            return ret, contexts
        pl.benchmark.update_benchmark_data(benchmark_index, CompType.GENERATOR, time.perf_counter() - start)
        pl.benchmark.insert_llm_data(benchmark_index, input_token_size)
    
    cleanup_pipeline_resources(retri_res, post_res, np_types, sub_questionss_result)
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
    elif target_generator.inference_type in (InferenceType.VLLM, InferenceType.OVMS):
        ret = await target_generator.run_remote(chat_request, [], np_type)
    else:
        raise ValueError("LLM inference_type not supported")
    return ret

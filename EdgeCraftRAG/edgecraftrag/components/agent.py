# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from abc import abstractmethod

from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.base import BaseComponent, CallbackType, CompType
from edgecraftrag.components.agents.utils import remove_think_tags
from edgecraftrag.utils import stream_generator
from langgraph.config import get_stream_writer
from pydantic import model_serializer


class Agent(BaseComponent):

    def __init__(self, name, agent_type, pipeline_idx, configs):
        super().__init__(name=name, comp_type=CompType.AGENT, comp_subtype=agent_type)
        if self.name == "" or self.name is None:
            self.name = self.idx
        self.enable_benchmark = os.getenv("ENABLE_BENCHMARK", "False").lower() == "true"
        self.pipeline_idx = pipeline_idx
        self.manager = None
        self.configs = configs

    @classmethod
    @abstractmethod
    def get_default_configs(cls):
        pass

    def get_bound_pipeline(self):
        if self.manager is not None:
            pl = self.manager.get_pipeline_by_name_or_id(self.pipeline_idx)
            return pl
        raise ValueError("No pipeline bound or bound pipeline not found")

    def get_active_knowledge_base(self):
        if self.manager is not None:
            kb = self.manager.get_active_knowledge_base()
            return kb
        return None

    async def llm_generate(self, request: ChatCompletionRequest, streaming):
        request.stream = streaming
        request.messages = self._messages
        response = await self._run_pipeline_generate(request)
        return response

    async def llm_generate_astream_writer(self, request, prefix=None, suffix=None) -> str:
        response = ""
        writer = get_stream_writer()
        first = True
        generator = await self.llm_generate(request, True)
        async for chunk in generator:
            if first and prefix:
                writer(prefix + chunk)
                first = False
            else:
                writer(chunk)
            response += chunk
        if suffix:
            writer(suffix)
        response = remove_think_tags(response)
        return response

    # wrappers for calling pipeline
    async def run_pipeline_chatqna(self, request):
        pl = self.get_bound_pipeline()
        if pl is not None:
            return await pl.run(cbtype=CallbackType.PIPELINE, chat_request=request)

    async def _run_pipeline_generate(self, request):
        pl = self.get_bound_pipeline()
        if pl is not None:
            return await pl.run(cbtype=CallbackType.GENERATE, chat_request=request)

    async def run_pipeline_retrieve_and_rerank(self, request):
        pl = self.get_bound_pipeline()
        if pl is not None:
            return await pl.run(cbtype=CallbackType.RETRIEVE_POSTPROCESS, chat_request=request)

    async def run_pipeline_retrieve(self, request):
        pl = self.get_bound_pipeline()
        if pl is not None:
            return await pl.run(cbtype=CallbackType.RETRIEVE, chat_request=request)

    async def run_pipeline_rerank(self, request, contexts):
        pl = self.get_bound_pipeline()
        if pl is not None:
            return await pl.run(cbtype=CallbackType.POSTPROCESS, chat_request=request, contexts=contexts)

    async def run_pipeline_query_search(self, request):
        pl = self.get_bound_pipeline()
        if pl is not None:
            return await pl.run(cbtype=CallbackType.QUERYSEARCH, chat_request=request)

    @model_serializer
    def ser_model(self):
        isactive = True if self.idx == self.manager.get_active_agent_id() else False
        set = {
            "idx": self.idx,
            "name": self.name,
            "type": self.comp_subtype,
            "pipeline_idx": self.pipeline_idx,
            "configs": self.configs,
            "active": isactive,
        }
        return set


async def stream_writer(input):
    writer = get_stream_writer()
    async for chunk in stream_generator(input):
        writer(chunk)

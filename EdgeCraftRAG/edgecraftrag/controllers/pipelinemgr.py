# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import gc
from typing import Any, List

from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.base import BaseMgr, CallbackType
from edgecraftrag.components.pipeline import Pipeline
from edgecraftrag.controllers.nodemgr import NodeMgr
from llama_index.core.schema import Document


class PipelineMgr(BaseMgr):

    def __init__(self):
        self._active_pipeline = None
        self._lock = asyncio.Lock()
        super().__init__()

    def create_pipeline(self, request, origin_json: str):
        if isinstance(request, str):
            name = request
            idx, documents_cache = None, None
        else:
            name = request.name
            idx = request.idx
            documents_cache = request.documents_cache
        pl = Pipeline(name, origin_json, idx, documents_cache)
        self.add(pl)
        return pl

    def get_pipeline_by_name_or_id(self, name: str):
        for _, pl in self.components.items():
            if pl.name == name or pl.idx == name:
                return pl
        return None

    def remove_pipeline_by_name_or_id(self, name: str):
        pl = self.get_pipeline_by_name_or_id(name)
        if pl is None:
            raise Exception("Pipeline not found...")
        if pl.status.active:
            raise Exception("Unable to remove an active pipeline...")
        pl.node_parser = None
        pl.indexer = None
        pl.retriever = None
        pl.postprocessor = None
        pl.generator = None
        pl.benchmark = None
        pl.status = None
        pl.run_pipeline_cb = None
        pl.run_retriever_cb = None
        pl.run_data_prepare_cb = None
        pl._node_changed = None
        self.remove(pl.idx)
        del pl
        gc.collect()
        return "Pipeline removed successfully"

    def get_pipelines(self):
        return [pl for _, pl in self.components.items()]

    def activate_pipeline(self, name: str, active: bool, nm: NodeMgr, kb_name: None):
        pl = self.get_pipeline_by_name_or_id(name)
        if pl is None:
            return

        if not active:
            pl.status.active = False
            self._active_pipeline = None
            return

        nodelist = None
        # if pl.node_changed:
        #     nodelist = nm.get_nodes(pl.node_parser.idx)
        pl.check_active(nodelist, kb_name)
        prevactive = self._active_pipeline
        if prevactive:
            prevactive.status.active = False
            prevactive.update_pipeline_json({"active": prevactive.status.active})
        pl.status.active = True
        self._active_pipeline = pl

    def get_active_pipeline(self) -> Pipeline:
        return self._active_pipeline

    def notify_node_change(self):
        for _, pl in self.components.items():
            pl.set_node_change()

    async def run_pipeline(self, chat_request: ChatCompletionRequest) -> Any:
        ap = self.get_active_pipeline()
        if ap is not None:
            return await ap.run(cbtype=CallbackType.PIPELINE, chat_request=chat_request)
        return -1

    async def run_retrieve_postprocess(self, chat_request: ChatCompletionRequest) -> Any:
        ap = self.get_active_pipeline()
        out = None
        if ap is not None:
            out = await ap.run(cbtype=CallbackType.RETRIEVE_POSTPROCESS, chat_request=chat_request)
            return out
        return -1

    async def run_retrieve(self, chat_request: ChatCompletionRequest) -> Any:
        ap = self.get_active_pipeline()
        out = None
        if ap is not None:
            out = await ap.run(cbtype=CallbackType.RETRIEVE, chat_request=chat_request)
            return out
        return -1

    async def run_postprocess(self, chat_request: ChatCompletionRequest, contexts) -> Any:
        ap = self.get_active_pipeline()
        out = None
        if ap is not None:
            out = await ap.run(cbtype=CallbackType.POSTPROCESS, chat_request=chat_request, contexts=contexts)
            return out
        return -1

    async def run_data_prepare(self, docs: List[Document]) -> Any:
        ap = self.get_active_pipeline()
        if ap is not None:
            return await ap.run(cbtype=CallbackType.DATAPREP, docs=docs)
        return -1

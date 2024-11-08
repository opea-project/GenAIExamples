# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from edgecraftrag.base import BaseComponent, CompType, PostProcessorType
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from pydantic import model_serializer


class RerankProcessor(BaseComponent):

    def __init__(self, rerank_model, top_n):
        BaseComponent.__init__(
            self,
            comp_type=CompType.POSTPROCESSOR,
            comp_subtype=PostProcessorType.RERANKER,
        )
        self.model = rerank_model
        self.top_n = top_n

    def run(self, **kwargs) -> Any:
        self.model.top_n = self.top_n
        query_bundle = None
        query_str = None
        if "retri_res" in kwargs:
            nodes = kwargs["retri_res"]
        if "query_bundle" in kwargs:
            query_bundle = kwargs["query_bundle"]
        if "query_str" in kwargs:
            query_str = kwargs["query_str"]
        return self.model.postprocess_nodes(nodes, query_bundle=query_bundle, query_str=query_str)

    @model_serializer
    def ser_model(self):
        set = {"idx": self.idx, "postprocessor_type": self.comp_subtype, "model": self.model, "top_n": self.top_n}
        return set


class MetadataReplaceProcessor(BaseComponent, MetadataReplacementPostProcessor):

    def __init__(self, target_metadata_key="window"):
        BaseComponent.__init__(
            self,
            target_metadata_key=target_metadata_key,
            comp_type=CompType.POSTPROCESSOR,
            comp_subtype=PostProcessorType.METADATAREPLACE,
        )

    def run(self, **kwargs) -> Any:
        query_bundle = None
        query_str = None
        if "retri_res" in kwargs:
            nodes = kwargs["retri_res"]
        if "query_bundle" in kwargs:
            query_bundle = kwargs["query_bundle"]
        if "query_str" in kwargs:
            query_str = kwargs["query_str"]
        return self.postprocess_nodes(nodes, query_bundle=query_bundle, query_str=query_str)

    @model_serializer
    def ser_model(self):
        set = {"idx": self.idx, "postprocessor_type": self.comp_subtype, "model": None, "top_n": None}
        return set

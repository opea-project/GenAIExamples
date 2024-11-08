# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from edgecraftrag.base import BaseComponent, CompType, NodeParserType
from llama_index.core.node_parser import HierarchicalNodeParser, SentenceSplitter, SentenceWindowNodeParser
from pydantic import model_serializer


class SimpleNodeParser(BaseComponent, SentenceSplitter):

    # Use super for SentenceSplitter since it's __init__ will cleanup
    # BaseComponent fields
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comp_type = CompType.NODEPARSER
        self.comp_subtype = NodeParserType.SIMPLE

    def run(self, **kwargs) -> Any:
        for k, v in kwargs.items():
            if k == "docs":
                return self.get_nodes_from_documents(v, show_progress=False)

        return None

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "parser_type": self.comp_subtype,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }
        return set


class HierarchyNodeParser(BaseComponent, HierarchicalNodeParser):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comp_type = CompType.NODEPARSER
        self.comp_subtype = NodeParserType.HIERARCHY

    def run(self, **kwargs) -> Any:
        for k, v in kwargs.items():
            if k == "docs":
                return self.get_nodes_from_documents(v, show_progress=False)

        return None

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "parser_type": self.comp_subtype,
            "chunk_size": self.chunk_sizes,
            "chunk_overlap": None,
        }
        return set


class SWindowNodeParser(BaseComponent, SentenceWindowNodeParser):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comp_type = CompType.NODEPARSER
        self.comp_subtype = NodeParserType.SENTENCEWINDOW

    def run(self, **kwargs) -> Any:
        for k, v in kwargs.items():
            if k == "docs":
                return self.get_nodes_from_documents(v, show_progress=False)

        return None

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "parser_type": self.comp_subtype,
            "chunk_size": None,
            "chunk_overlap": None,
        }
        return set

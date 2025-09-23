# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from edgecraftrag.api_schema import IndexerIn, ModelIn, NodeParserIn
from edgecraftrag.base import BaseComponent, BaseMgr, CallbackType, ModelType, NodeParserType


class NodeParserMgr(BaseMgr):

    def __init__(self):
        super().__init__()

    def search_parser(self, npin: NodeParserIn) -> BaseComponent:
        for _, v in self.components.items():
            v_parser_type = v.comp_subtype
            if v_parser_type == npin.parser_type:
                if v_parser_type == NodeParserType.HIERARCHY and v.chunk_sizes == npin.chunk_sizes:
                    return v
                elif v_parser_type == NodeParserType.SENTENCEWINDOW and v.window_size == npin.window_size:
                    return v
                elif (
                    v_parser_type == NodeParserType.SIMPLE
                    and v.chunk_size == npin.chunk_size
                    and v.chunk_overlap == npin.chunk_overlap
                ):
                    return v
        return None

    def search_parser_change(self, pl, req):
        pl_change = False
        try:
            if pl.node_parser.comp_subtype != req.node_parser.parser_type:
                return True
            if pl.node_parser.comp_subtype == req.node_parser.parser_type:
                if pl.node_parser.comp_subtype == NodeParserType.SIMPLE:
                    if (
                        pl.node_parser.chunk_size != req.node_parser.chunk_size
                        or pl.node_parser.chunk_overlap != req.node_parser.chunk_overlap
                    ):
                        pl_change = True
                elif pl.node_parser.comp_subtype == NodeParserType.SENTENCEWINDOW:
                    if pl.node_parser.window_size != req.node_parser.window_size:
                        pl_change = True
                elif pl.node_parser.comp_subtype == NodeParserType.HIERARCHY:
                    if pl.node_parser.chunk_sizes != req.node_parser.chunk_sizes:
                        pl_change = True
                elif pl.node_parser.comp_subtype == NodeParserType.UNSTRUCTURED:
                    if (
                        pl.node_parser.chunk_size != req.node_parser.chunk_size
                        or pl.node_parser.chunk_overlap != req.node_parser.chunk_overlap
                    ):
                        pl_change = True
        except:
            return False
        return pl_change


class IndexerMgr(BaseMgr):

    def __init__(self):
        super().__init__()

    def search_indexer(self, indin: IndexerIn) -> BaseComponent:
        for _, v in self.components.items():
            if v.comp_subtype == indin.indexer_type:
                if (
                    hasattr(v, "model")
                    and v.model
                    and indin.embedding_model
                    and (
                        (v.model.model_id_or_path == indin.embedding_model.model_id)
                        or (v.model.model_id_or_path == indin.embedding_model.model_path)
                    )
                    and v.model.device == indin.embedding_model.device
                ):
                    return v
        return None


class RetrieverMgr(BaseMgr):

    def __init__(self):
        super().__init__()


class PostProcessorMgr(BaseMgr):

    def __init__(self):
        super().__init__()


class GeneratorMgr(BaseMgr):

    def __init__(self):
        super().__init__()

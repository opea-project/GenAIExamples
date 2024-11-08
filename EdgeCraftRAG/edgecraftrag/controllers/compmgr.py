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

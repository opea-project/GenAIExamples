# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from edgecraftrag.controllers.compmgr import GeneratorMgr, IndexerMgr, NodeParserMgr, PostProcessorMgr, RetrieverMgr
from edgecraftrag.controllers.filemgr import FilelMgr
from edgecraftrag.controllers.modelmgr import ModelMgr
from edgecraftrag.controllers.nodemgr import NodeMgr
from edgecraftrag.controllers.pipelinemgr import PipelineMgr


class Context:

    def __init__(self):
        self.plmgr = PipelineMgr()
        self.nodemgr = NodeMgr()
        self.npmgr = NodeParserMgr()
        self.idxmgr = IndexerMgr()
        self.rtvmgr = RetrieverMgr()
        self.ppmgr = PostProcessorMgr()
        self.modmgr = ModelMgr()
        self.genmgr = GeneratorMgr()
        self.filemgr = FilelMgr()

    def get_pipeline_mgr(self):
        return self.plmgr

    def get_node_mgr(self):
        return self.nodemgr

    def get_node_parser_mgr(self):
        return self.npmgr

    def get_indexer_mgr(self):
        return self.idxmgr

    def get_retriever_mgr(self):
        return self.rtvmgr

    def get_postprocessor_mgr(self):
        return self.ppmgr

    def get_model_mgr(self):
        return self.modmgr

    def get_generator_mgr(self):
        return self.genmgr

    def get_file_mgr(self):
        return self.filemgr


ctx = Context()

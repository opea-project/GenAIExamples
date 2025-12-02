# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from edgecraftrag.controllers.agentmgr import AgentManager
from edgecraftrag.controllers.compmgr import (
    GeneratorMgr,
    IndexerMgr,
    NodeParserMgr,
    PostProcessorMgr,
    RetrieverMgr,
)
from edgecraftrag.controllers.filemgr import FilelMgr
from edgecraftrag.controllers.knowledge_basemgr import KnowledgeManager
from edgecraftrag.controllers.modelmgr import ModelMgr
from edgecraftrag.controllers.nodemgr import NodeMgr
from edgecraftrag.controllers.pipelinemgr import PipelineMgr
from edgecraftrag.controllers.sessionmgr import SessionManager


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
        self.knowledgemgr = KnowledgeManager()
        self.agentmgr = AgentManager(self.plmgr)
        self.sessionmgr = SessionManager()

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

    def get_knowledge_mgr(self):
        return self.knowledgemgr

    def get_agent_mgr(self):
        return self.agentmgr

    def get_session_mgr(self):
        return self.sessionmgr


ctx = Context()

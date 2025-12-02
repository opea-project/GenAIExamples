# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, Optional

from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.api_schema import AgentCreateIn
from edgecraftrag.base import AgentType, BaseMgr, CallbackType
from edgecraftrag.components.agent import Agent
from edgecraftrag.components.agents.deep_search.deep_search import DeepSearchAgent
from edgecraftrag.components.agents.simple import SimpleRAGAgent


class AgentManager(BaseMgr):

    active_agent_idx: Optional[str] = None

    def __init__(self, pipeline_mgr):
        super().__init__()
        self.active_agent_idx = None
        self.agents = {}
        self.pipeline_mgr = pipeline_mgr

    def set_manager(self, agent: Agent):
        agent.manager = self

    def get_pipeline_by_name_or_id(self, name_or_id):
        return self.pipeline_mgr.get_pipeline_by_name_or_id(name_or_id)

    def get_agents(self) -> Dict[str, Any]:
        return self.agents

    def get_agent_by_id(self, idx):
        return self.agents.get(idx, None)

    def get_agent_by_name(self, name):
        for k, a in self.agents.items():
            if a.name == name:
                return a
        return None

    def get_agent_id_by_name(self, name):
        for k, a in self.agents.items():
            if a.name == name:
                return k
        return None

    def create_agent(self, cfgs: AgentCreateIn):
        new_agent = None
        if not self.get_pipeline_by_name_or_id(cfgs.pipeline_idx):
            return "Create Agent failed. Pipeline id not found."
        if cfgs.type == AgentType.SIMPLE:
            new_agent = SimpleRAGAgent(cfgs.idx, cfgs.name, cfgs.pipeline_idx, cfgs.configs)
        elif cfgs.type == AgentType.DEEPSEARCH:
            new_agent = DeepSearchAgent(cfgs.idx, cfgs.name, cfgs.pipeline_idx, cfgs.configs)
        if new_agent is not None:
            self.set_manager(new_agent)
            self.agents[new_agent.idx] = new_agent
            if cfgs.active:
                self.active_agent_idx = new_agent.idx
            return new_agent
        else:
            return "Create Agent failed."

    def update_agent(self, name, cfgs: AgentCreateIn):
        idx = self.get_agent_id_by_name(name)
        if idx:
            agent = self.get_agent_by_id(idx)
            if cfgs.configs:
                agent.update(cfgs.configs)
            if cfgs.active:
                return self.activate_agent(idx)
            else:
                return self.deactivate_agent(idx)
            return True
        else:
            return False

    def remove_agent(self, name):
        idx = self.get_agent_id_by_name(name)
        if self.agents.pop(idx, None):
            return True
        return False

    def activate_agent(self, idx):
        if idx in self.agents:
            self.active_agent_idx = idx
            return True
        else:
            return False

    def deactivate_agent(self, idx):
        if idx in self.agents:
            self.active_agent_idx = None
            return True
        else:
            return False

    def get_active_agent_id(self):
        return self.active_agent_idx

    def get_active_agent(self):
        if self.active_agent_idx:
            return self.agents[self.active_agent_idx]
        else:
            return None

    def get_agent_default_configs(self, agent_type):
        if agent_type == AgentType.SIMPLE:
            return SimpleRAGAgent.get_default_configs()
        if agent_type == AgentType.DEEPSEARCH:
            return DeepSearchAgent.get_default_configs()

    async def run_agent(self, chat_request: ChatCompletionRequest) -> Any:
        active_agent = self.get_active_agent()
        if active_agent is not None:
            return await active_agent.run(cbtype=CallbackType.RUNAGENT, chat_request=chat_request)

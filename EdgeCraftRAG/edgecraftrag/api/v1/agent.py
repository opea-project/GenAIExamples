# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import time

from edgecraftrag.api.v1.knowledge_base import Synchronizing_vector_data
from edgecraftrag.api_schema import AgentCreateIn
from edgecraftrag.base import AgentType
from edgecraftrag.config_repository import MilvusConfigRepository, save_agent_configurations
from edgecraftrag.context import ctx
from edgecraftrag.env import AGENT_FILE
from fastapi import FastAPI, HTTPException, status

agent_app = FastAPI()


# GET Agents
@agent_app.get(path="/v1/settings/agents")
async def get_all_agents():
    out = []
    agents = ctx.get_agent_mgr().get_agents()
    active_id = ctx.get_agent_mgr().get_active_agent_id()
    for k, agent in agents.items():
        pipeline_name = ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(agent.pipeline_idx).name
        out.append(
            AgentCreateIn(
                idx=agent.idx,
                name=agent.name,
                type=agent.comp_subtype,
                pipeline_idx=agent.pipeline_idx,
                pipeline_name=pipeline_name,
                configs=agent.configs,
                active=True if agent.idx == active_id else False,
            )
        )
    return out


# GET Agent
@agent_app.get(path="/v1/settings/agents/{name}")
async def get_agent(name):
    agent = ctx.get_agent_mgr().get_agent_by_name(name)
    if agent:
        pipeline_name = ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(agent.pipeline_idx).name
        isactive = True if agent.idx == ctx.get_agent_mgr().get_active_agent_id() else False
        return AgentCreateIn(
            idx=agent.idx,
            name=agent.name,
            type=agent.comp_subtype,
            pipeline_idx=agent.pipeline_idx,
            pipeline_name=pipeline_name,
            configs=agent.configs,
            active=isactive,
        )
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


# POST Agent
@agent_app.post(path="/v1/settings/agents")
async def create_agent(request: AgentCreateIn, status_code=status.HTTP_201_CREATED):
    try:
        agent = ctx.get_agent_mgr().create_agent(request)
        if agent:
            await save_agent_configurations("add", ctx.get_agent_mgr().get_agents())
        return agent
    except (ValueError, Exception) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# PATCH Agent
@agent_app.patch(path="/v1/settings/agents/{name}")
async def update_agent(name, request: AgentCreateIn):
    try:
        agentmgr = ctx.get_agent_mgr()
        agent = agentmgr.get_agent_by_name(name)
        if agent:
            ret = agentmgr.update_agent(name, request)
            if ret:
                await save_agent_configurations("update", ctx.get_agent_mgr().get_agents())
                # manage agent bound pipeline status, trigger kb indexing if needed
                # can be removed once kb indexing is decoupled from pipeline
                pl_idx = agent.pipeline_idx
                await manage_agent_bound_pipeline(pl_idx, request)
            return ret
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except (ValueError, Exception) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# DELETE Agent
@agent_app.delete(path="/v1/settings/agents/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(name):
    try:
        agentmgr = ctx.get_agent_mgr()
        if agentmgr.get_agent_by_name(name):
            if agentmgr.remove_agent(name):
                await save_agent_configurations("delete", ctx.get_agent_mgr().get_agents())
                return
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except (ValueError, Exception) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# GET Agent Type default configs
@agent_app.get(path="/v1/settings/agents/configs/{agent_type}")
async def get_agent_default_configs(agent_type):
    try:
        if agent_type in [e.value for e in AgentType]:
            return ctx.get_agent_mgr().get_agent_default_configs(agent_type)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except (ValueError, Exception) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Restore agent configurations
async def restore_agent_configurations():
    milvus_repo = MilvusConfigRepository.create_connection("agent_config", 1)
    all_agents = []
    if milvus_repo:
        time.sleep(10)
        all_agents_repo = milvus_repo.get_configs()
        for agent in all_agents_repo:
            all_agents.append(agent.get("config_json"))
    else:
        if os.path.exists(AGENT_FILE):
            with open(AGENT_FILE, "r", encoding="utf-8") as f:
                all_agents = f.read()
        if all_agents:
            all_agents = json.loads(all_agents)
    try:
        for agent_data in all_agents:
            agent_req = AgentCreateIn(**agent_data)
            await load_agent(agent_req)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


async def load_agent(request: AgentCreateIn):
    agentmgr = ctx.get_agent_mgr()
    agent = agentmgr.get_agent_by_name(request.name)
    if agent is None:
        # TODO: Restore idx back
        # TODO: Update agent by import a json
        agent = agentmgr.create_agent(request)
    try:
        await save_agent_configurations("add", ctx.get_agent_mgr().get_agents())
    except (ValueError, Exception) as e:
        agentmgr.remove_agent_by_name(request.name)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return agent


async def manage_agent_bound_pipeline(bound_pl_idx, request):
    # case1: activate agent, while bound pipeline is not active -> activate it, cache previous active pipeline if exists
    # case2: activate agent, while bound pipeline is already active -> still call activate, for caching current pipeline
    # case3: deactivate agent, while bound pipeline **was** active -> do NOT deactivate bound pipeline, do nothing
    # case4: deactivate agent, while bound pipeline **was NOT** active -> deactivate bound pipeline, activate previous active pipeline if exists
    pl_manager = ctx.get_pipeline_mgr()
    prev_active_pipeline = pl_manager.get_active_pipeline()

    active_kb = ctx.knowledgemgr.get_active_knowledge_base()
    kb_name = active_kb.name if active_kb else "default"

    if request.active:
        pl_manager.activate_pipeline(bound_pl_idx, request.active, ctx.get_node_mgr(), kb_name, cache_prev=True)
    else:
        # at deactivate, prev_active_pl can be 1.other pl/2.None/3.current bound_pl
        prev_active_pl = pl_manager.get_prev_active_pipeline_name()
        if prev_active_pl and prev_active_pl != bound_pl_idx:
            # 1, restore to the other pipeline activated
            pl_manager.activate_pipeline(prev_active_pl, True, ctx.get_node_mgr(), kb_name)
        elif not prev_active_pl:
            # 2, deactivate current bound pipeline, leave no active pipeline as before
            pl_manager.activate_pipeline(bound_pl_idx, False, ctx.get_node_mgr(), kb_name)
        else:
            # 3, do nothing
            pass
        # when agent is deactivated, clear cached previous active pipeline
        pl_manager.clear_prev_active_pipeline_name()

    cur_active_pipeline = pl_manager.get_active_pipeline()
    if prev_active_pipeline and cur_active_pipeline and prev_active_pipeline.idx != cur_active_pipeline.idx:
        await Synchronizing_vector_data(prev_active_pipeline, cur_active_pipeline)

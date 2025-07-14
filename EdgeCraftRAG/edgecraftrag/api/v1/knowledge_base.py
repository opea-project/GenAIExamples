# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import re

from edgecraftrag.api.v1.data import add_data
from edgecraftrag.api_schema import DataIn, KnowledgeBaseCreateIn
from edgecraftrag.base import IndexerType
from edgecraftrag.context import ctx
from fastapi import FastAPI, HTTPException, status
from pymilvus.exceptions import MilvusException

kb_app = FastAPI()


# Get all knowledge bases
@kb_app.get(path="/v1/knowledge")
async def get_all_knowledge_bases():
    try:
        return ctx.knowledgemgr.get_all_knowledge_bases()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Get the specified knowledge base.
@kb_app.get("/v1/knowledge/{knowledge_name}")
async def get_knowledge_base(knowledge_name: str):
    kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge_name)
    return kb


# Create a new knowledge base
@kb_app.post(path="/v1/knowledge")
async def create_knowledge_base(knowledge: KnowledgeBaseCreateIn):
    try:
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", knowledge.name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base names must begin with a letter or an underscore and contain only letters, numbers, and underscores",
            )
        kb = ctx.knowledgemgr.create_knowledge_base(knowledge)
        if active_pl.indexer.comp_subtype == "milvus_vector" and kb.active:
            active_pl.indexer.reinitialize_indexer(kb.name)
            active_pl.update_indexer_to_retriever()
        await save_knowledge_to_file()
        return "Create knowledge base successfully"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Delete the knowledge base by name
@kb_app.delete(path="/v1/knowledge/{knowledge_name}")
async def delete_knowledge_base(knowledge_name: str):
    try:
        active_kb = ctx.knowledgemgr.get_active_knowledge_base()
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        if active_kb.name == knowledge_name or active_kb.idx == knowledge_name:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot delete a running knowledge base."
            )
        if active_pl.indexer.comp_subtype == "milvus_vector":
            await remove_file_handler([], knowledge_name)
        if active_kb:
            active_pl.indexer.reinitialize_indexer(active_kb.name)
            active_pl.update_indexer_to_retriever()
        result = ctx.knowledgemgr.delete_knowledge_base(knowledge_name)
        await save_knowledge_to_file()
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Switch the active knowledge base
@kb_app.patch(path="/v1/knowledge/patch")
async def update_knowledge_base(knowledge: KnowledgeBaseCreateIn):
    try:
        kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge.name)
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        if active_pl.indexer.comp_subtype != "milvus_vector":
            if knowledge.active and knowledge.active != kb.active:
                file_paths = kb.get_file_paths()
                await update_knowledge_base_handler(file_paths, knowledge.name)
            elif not knowledge.active:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Must have an active knowledge base"
                )
        else:
            if knowledge.active and knowledge.active != kb.active:
                active_pl.indexer.reinitialize_indexer(knowledge.name)
                active_pl.update_indexer_to_retriever()
            elif not knowledge.active:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Must have an active knowledge base"
                )
        result = ctx.knowledgemgr.update_knowledge_base(knowledge)
        await save_knowledge_to_file()
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Add a files to the knowledge base
@kb_app.post(path="/v1/knowledge/{knowledge_name}/files")
async def add_file_to_knowledge_base(knowledge_name, file_path: DataIn):
    try:
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge_name)
        if os.path.isdir(file_path.local_path):
            for root, _, files in os.walk(file_path.local_path):
                for file in files:
                    file_full_path = os.path.join(root, file)
                    if file_full_path not in kb.get_file_paths():
                        kb.add_file_path(file_full_path)
                    else:
                        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="File upload failed")
        elif os.path.isfile(file_path.local_path) and file_path.local_path not in kb.get_file_paths():
            kb.add_file_path(file_path.local_path)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File upload failed")

        active_kb = ctx.knowledgemgr.get_active_knowledge_base()
        kb_file_path = kb.get_file_paths()
        if active_pl.indexer.comp_subtype == "milvus_vector":
            if active_kb:
                if active_kb.name == knowledge_name or active_kb.idx == knowledge_name:
                    active_pl.indexer.reinitialize_indexer(active_kb.name)
                    active_pl.update_indexer_to_retriever()
                    await update_knowledge_base_handler(file_path, knowledge_name, add_file=True)
                else:
                    await update_knowledge_base_handler(kb_file_path, knowledge_name)
                    active_pl.indexer.reinitialize_indexer(active_kb.name)
                    active_pl.update_indexer_to_retriever()
            else:
                await update_knowledge_base_handler(kb_file_path, knowledge_name)
                active_pl.indexer.reinitialize_indexer(active_kb.name)
                active_pl.update_indexer_to_retriever()
        else:
            if active_kb:
                if active_kb.name == knowledge_name or active_kb.idx == knowledge_name:
                    await update_knowledge_base_handler(file_path, knowledge_name, add_file=True)

        await save_knowledge_to_file()
        return "File upload successfully"
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Remove a file from the knowledge base
@kb_app.delete(path="/v1/knowledge/{knowledge_name}/files")
async def remove_file_from_knowledge_base(knowledge_name, file_path: DataIn):
    try:
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge_name)
        active_kb = ctx.knowledgemgr.get_active_knowledge_base()
        if file_path.local_path in kb.get_file_paths():
            kb.remove_file_path(file_path.local_path)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File remove failure")

        kb_file_path = kb.get_file_paths()
        if active_pl.indexer.comp_subtype == "milvus_vector":
            if active_kb:
                if active_kb.name == knowledge_name or active_kb.idx == knowledge_name:
                    await remove_file_handler(kb_file_path, knowledge_name)
                else:
                    await remove_file_handler(kb_file_path, knowledge_name)
                    active_pl.indexer.reinitialize_indexer(active_kb.name)
                    active_pl.update_indexer_to_retriever()
            else:
                await remove_file_handler(kb_file_path, knowledge_name)
                active_pl.indexer.reinitialize_indexer(active_kb.name)
                active_pl.update_indexer_to_retriever()
        elif active_kb:
            if active_kb.name == knowledge_name or active_kb.idx == knowledge_name:
                await update_knowledge_base_handler(kb_file_path, knowledge_name)
        await save_knowledge_to_file()
        return "File deleted successfully"
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Update knowledge base data
async def update_knowledge_base_handler(file_path=None, knowledge_name: str = "default_kb", add_file: bool = False):
    if ctx.get_pipeline_mgr().get_active_pipeline() is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Please activate pipeline")

    pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if add_file and file_path:
        return await add_data(file_path)
    else:
        try:
            ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
            pl.indexer.reinitialize_indexer(knowledge_name)
            pl.update_indexer_to_retriever()
            if file_path:
                for file in file_path:
                    request = DataIn(local_path=file)
                    await add_data(request)
        except MilvusException as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        return "Done"


# Update knowledge base data
async def remove_file_handler(file_path=None, knowledge_name: str = "default_kb"):
    if ctx.get_pipeline_mgr().get_active_pipeline() is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Please activate pipeline")

    pl = ctx.get_pipeline_mgr().get_active_pipeline()
    ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
    try:
        pl.indexer.clear_milvus_collection(knowledge_name)
        pl.indexer.reinitialize_indexer(knowledge_name)
    except MilvusException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    pl.update_indexer_to_retriever()
    if file_path:
        for file in file_path:
            request = DataIn(local_path=file)
            await add_data(request)
    return "Done"


# Restore knowledge base configuration
async def load_knowledge_from_file():
    CONFIG_DIR = "/home/user/ui_cache/configs"
    KNOWLEDGEBASE_FILE = os.path.join(CONFIG_DIR, "knowledgebase.json")
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if os.path.exists(KNOWLEDGEBASE_FILE):
        with open(KNOWLEDGEBASE_FILE, "r") as f:
            all_Knowledgebases = f.read()
        try:
            all_data = json.loads(all_Knowledgebases)
            for Knowledgebase_data in all_data:
                pipeline_req = KnowledgeBaseCreateIn(**Knowledgebase_data)
                kb = ctx.knowledgemgr.create_knowledge_base(pipeline_req)
                if Knowledgebase_data["file_map"]:
                    if active_pl.indexer.comp_subtype != "milvus_vector" and Knowledgebase_data["active"]:
                        for file_path in Knowledgebase_data["file_map"].values():
                            await update_knowledge_base_handler(
                                DataIn(local_path=file_path), Knowledgebase_data["name"], add_file=True
                            )
                            kb.add_file_path(file_path)
                    elif Knowledgebase_data["active"]:
                        active_pl.indexer.reinitialize_indexer(Knowledgebase_data["name"])
                        active_pl.update_indexer_to_retriever()
                        for file_path in Knowledgebase_data["file_map"].values():
                            kb.add_file_path(file_path)
                    else:
                        for file_path in Knowledgebase_data["file_map"].values():
                            kb.add_file_path(file_path)
        except Exception as e:
            print(f"Error load Knowledge base: {e}")


# Configuration of knowledge base for persistence
async def save_knowledge_to_file():
    CONFIG_DIR = "/home/user/ui_cache/configs"
    KNOWLEDGEBASE_FILE = os.path.join(CONFIG_DIR, "knowledgebase.json")
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        kb_base = ctx.knowledgemgr.get_all_knowledge_bases()
        knowledgebases_data = []
        for kb in kb_base:
            kb_json = {"name": kb.name, "description": kb.description, "active": kb.active, "file_map": kb.file_map}
            knowledgebases_data.append(kb_json)
        json_str = json.dumps(knowledgebases_data, indent=2)
        with open(KNOWLEDGEBASE_FILE, "w") as f:
            f.write(json_str)
    except Exception as e:
        print(f"Error saving Knowledge base: {e}")

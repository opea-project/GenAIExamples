# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from edgecraftrag.api.v1.data import add_data
from edgecraftrag.api_schema import DataIn, KnowledgeBaseCreateIn
from edgecraftrag.context import ctx
from fastapi import FastAPI, HTTPException, status

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
        kb = ctx.knowledgemgr.create_knowledge_base(knowledge)
        if kb.active:
            await update_knowledge_base_handler(kb.get_file_paths())
        return "Create knowledge base successfully"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Delete the knowledge base by name
@kb_app.delete(path="/v1/knowledge/{knowledge_name}")
async def delete_knowledge_base(knowledge_name: str):
    try:
        return ctx.knowledgemgr.delete_knowledge_base(knowledge_name)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Switch the active knowledge base
@kb_app.patch(path="/v1/knowledge/patch")
async def update_knowledge_base(knowledge: KnowledgeBaseCreateIn):
    try:
        kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge.name)
        if knowledge.active is not None and knowledge.active != kb.active:
            file_paths = kb.get_file_paths() if knowledge.active else None
            await update_knowledge_base_handler(file_paths)
        result = ctx.knowledgemgr.update_knowledge_base(knowledge)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Add a files to the  knowledge base
@kb_app.post(path="/v1/knowledge/{knowledge_name}/files")
async def add_file_to_knowledge_base(knowledge_name, file_path: DataIn):
    try:
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
        if active_kb:
            if active_kb.name == knowledge_name or active_kb.idx == knowledge_name:
                await update_knowledge_base_handler(file_path, add_file=True)

        return "File upload successfully"
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Remove a file from the knowledge base
@kb_app.delete(path="/v1/knowledge/{knowledge_name}/files")
async def remove_file_from_knowledge_base(knowledge_name, file_path: DataIn):
    try:
        kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge_name)
        if file_path.local_path in kb.get_file_paths():
            kb.remove_file_path(file_path.local_path)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File remove failure")

        file_path = kb.get_file_paths()
        active_kb = ctx.knowledgemgr.get_active_knowledge_base()
        if active_kb:
            if active_kb.name == knowledge_name or active_kb.idx == knowledge_name:
                await update_knowledge_base_handler(file_path)
        return "File deleted successfully"
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Update knowledge base data
async def update_knowledge_base_handler(file_path=None, add_file: bool = False):
    if ctx.get_pipeline_mgr().get_active_pipeline() is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Please activate pipeline")

    if add_file and file_path:
        return await add_data(file_path)

    elif file_path:
        pl = ctx.get_pipeline_mgr().get_active_pipeline()
        ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
        pl.indexer.reinitialize_indexer()
        pl.update_indexer_to_retriever()
        for file in file_path:
            request = DataIn(local_path=file)
            await add_data(request)
        return "Done"

    else:
        pl = ctx.get_pipeline_mgr().get_active_pipeline()
        ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
        pl.indexer.reinitialize_indexer()
        pl.update_indexer_to_retriever()
        return "Done"

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import copy
import json
import os
import re

from typing import List, Dict, Union
from edgecraftrag.api.v1.data import add_data
from edgecraftrag.api_schema import DataIn, KnowledgeBaseCreateIn, ExperienceIn
from edgecraftrag.base import IndexerType
from edgecraftrag.context import ctx
from edgecraftrag.utils import compare_mappings
from fastapi import FastAPI, HTTPException, status
from pymilvus.exceptions import MilvusException

kb_app = FastAPI()

# Define the root directory for knowledge base files
KNOWLEDGE_BASE_ROOT = "/home/user/ui_cache"


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
        if not active_pl:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Please activate pipeline")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", knowledge.name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base names must begin with a letter or underscore",
            )
        kb = ctx.knowledgemgr.create_knowledge_base(knowledge)
        if kb.active and kb.comp_type =="knowledge":
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
        rm_kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge_name)
        active_kb = ctx.knowledgemgr.get_active_knowledge_base()
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        if rm_kb.comp_type == "knowledge":
            if not active_kb:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Please activate a knowledge base before proceeding.")
            if active_kb.name == knowledge_name or active_kb.idx == knowledge_name:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot delete a running knowledge base.")
            kb_file_path = rm_kb.get_file_paths()
            if kb_file_path:
                if active_pl.indexer.comp_subtype == "milvus_vector":
                    await remove_file_handler([], knowledge_name)
                if active_kb:
                    active_pl.indexer.reinitialize_indexer(active_kb.name)
                    active_pl.update_indexer_to_retriever()
        if rm_kb.comp_type == "experience":
            if rm_kb.experience_active:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot delete a running experience knowledge base.")
            else:
                rm_kb.clear_experiences()
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
        if kb.comp_type == "knowledge":
            if active_pl.indexer.comp_subtype != "milvus_vector":
                if knowledge.active and knowledge.active != kb.active:
                    file_paths = kb.get_file_paths()
                    await update_knowledge_base_handler(file_paths, knowledge.name)
                elif not knowledge.active and kb.description != knowledge.description:
                    pass
                elif not knowledge.active:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Must have an active knowledge base"
                    )
            else:
                if knowledge.active and knowledge.active != kb.active:
                    active_pl.indexer.reinitialize_indexer(knowledge.name)
                    active_pl.update_indexer_to_retriever()
                elif not knowledge.active and kb.description != knowledge.description:
                    pass
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
        if kb.comp_type =="experience":
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The experience type cannot perform file operations.")
        # Validate and normalize the user-provided path
        user_path = file_path.local_path
        normalized_path = os.path.normpath(os.path.join(KNOWLEDGE_BASE_ROOT, user_path))
        if not normalized_path.startswith(KNOWLEDGE_BASE_ROOT):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path")
        if os.path.isdir(normalized_path):
            for root, _, files in os.walk(normalized_path):
                for file in files:
                    file_full_path = os.path.join(root, file)
                    if file_full_path not in kb.get_file_paths():
                        kb.add_file_path(file_full_path)
                    else:
                        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="File upload failed")
        elif os.path.isfile(normalized_path) and normalized_path not in kb.get_file_paths():
            kb.add_file_path(normalized_path)
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
        if kb.comp_type =="experience":
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The experience type cannot perform file operations.")
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

@kb_app.post("/v1/experience")
def get_experience_by_question(req: ExperienceIn):
    kb = ctx.knowledgemgr.get_experience_kb()   
    result = kb.get_experience_by_question(req.question)
    if not result:
        raise HTTPException(404, detail="Experience not found")
    return result

@kb_app.get("/v1/experiences")
def get_all_experience():
    kb = ctx.knowledgemgr.get_experience_kb()
    if kb:
        return kb.get_all_experience()
    else:
        return kb

@kb_app.patch("/v1/experiences")
def update_experience(experience: ExperienceIn):
    kb = ctx.knowledgemgr.get_experience_kb()
    result = kb.update_experience(experience.question, experience.content)
    if not result:
        raise HTTPException(404, detail=f"Question not found")
    return result

@kb_app.delete("/v1/experiences")
def delete_experience(req :ExperienceIn):
    kb = ctx.knowledgemgr.get_experience_kb()
    success = kb.delete_experience(req.question)
    if not success:
        raise HTTPException(404, detail=f"Question {req.question} not found")
    return {"message": f"Question deleted"}

@kb_app.post("/v1/multiple_experiences/check")
def check_duplicate_multiple_experiences(experiences: List[Dict[str, Union[str, List[str]]]]):
    kb = ctx.knowledgemgr.get_experience_kb()
    if not kb:
       raise HTTPException(404, detail=f"No active experience type knowledge base")
    all_existing = kb.get_all_experience()
    existing_questions = {item["question"] for item in all_existing}
    new_questions = [exp["question"] for exp in experiences if "question" in exp]
    duplicate_questions = [q for q in new_questions if q in existing_questions]
    if duplicate_questions:
        return {"code": 2001, "detail": "Duplicate experiences are appended OR overwritten!"}
    else:
        kb.add_multiple_experiences(experiences=experiences, flag=True)  
        return {"status": "success","detail": "No duplicate experiences, added successfully"}

@kb_app.post("/v1/multiple_experiences/confirm")
def confirm_multiple_experiences(experiences: List[Dict[str, Union[str, List[str]]]],flag: bool):
    kb = ctx.knowledgemgr.get_experience_kb()
    try:
        if not kb:
            raise HTTPException(404, detail=f"No active experience type knowledge base")
        kb.add_multiple_experiences(experiences=experiences, flag=flag)
        return {"status": "success", "detail": "Experiences added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Add Failure：{str(e)}")

@kb_app.post("/v1/experiences/files")
def add_experiences_from_file(req: DataIn):
    kb = ctx.knowledgemgr.get_experience_kb()
    try:
        kb.add_experiences_from_file(req.local_path)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
        with open(KNOWLEDGEBASE_FILE, "r", encoding="utf-8") as f:
            all_Knowledgebases = f.read()
        try:
            all_data = json.loads(all_Knowledgebases)
            for Knowledgebase_data in all_data:
                pipeline_req = KnowledgeBaseCreateIn(**Knowledgebase_data)
                kb = ctx.knowledgemgr.create_knowledge_base(pipeline_req)
                if  kb.comp_type =="knowledge":
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
            kb_json = {"name": kb.name, "description": kb.description, "active": kb.active, "file_map": kb.file_map, "comp_type": kb.comp_type, "experience_active": kb.experience_active}
            knowledgebases_data.append(kb_json)
        json_str = json.dumps(knowledgebases_data, indent=2, ensure_ascii=False)
        with open(KNOWLEDGEBASE_FILE, "w", encoding="utf-8") as f:
            f.write(json_str)
    except Exception as e:
        print(f"Error saving Knowledge base: {e}")


all_pipeline_milvus_maps = {}
current_pipeline_kb_map = {}
async def refresh_milvus_map(milvus_name):
    current_pipeline_kb_map.clear()
    knowledge_bases_list = await get_all_knowledge_bases()
    for kb in knowledge_bases_list:
        if kb.comp_type == "experience":
                    continue
        current_pipeline_kb_map[kb.name] = kb.file_map
    all_pipeline_milvus_maps[milvus_name] = copy.deepcopy(current_pipeline_kb_map)

async def Synchronizing_vector_data(old_active_pl, new_active_pl):
    try:
        active_kb = ctx.knowledgemgr.get_active_knowledge_base()
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        milvus_name = (
            old_active_pl.name + str(old_active_pl.indexer.model_extra["d"]) if old_active_pl else "default_kb"
        )
        if not active_kb:
            return True
        if not active_pl:
            if old_active_pl:
                if old_active_pl.indexer.comp_subtype == "milvus_vector":
                    await refresh_milvus_map(milvus_name)
            return True

        if new_active_pl.indexer.comp_subtype == "milvus_vector":
            new_milvus_map = {}
            kb_list = await get_all_knowledge_bases()
            for kb in kb_list:
                if kb.comp_type == "experience":
                    continue
                new_milvus_map[kb.name] = kb.file_map
            added_files, deleted_files = compare_mappings(
                new_milvus_map,
                all_pipeline_milvus_maps.get(new_active_pl.name + str(new_active_pl.indexer.model_extra["d"]), {}),
            )
            # Synchronization of deleted files
            for kb_name, file_paths in deleted_files.items():
                if file_paths:
                    new_active_pl.indexer.clear_milvus_collection(kb_name)
                    if kb_name not in new_milvus_map.keys():
                        continue
                    kb = await get_knowledge_base(kb_name)
                    new_active_pl.indexer.reinitialize_indexer(kb_name)
                    file_paths = kb.get_file_paths()
                    if file_paths:
                        for file in file_paths:
                            await add_data(DataIn(local_path=file))
            # Synchronization of added files
            for kb_name, file_paths in added_files.items():
                if file_paths:
                    for file_path in file_paths.values():
                        new_active_pl.indexer.reinitialize_indexer(kb_name)
                        await add_data(DataIn(local_path=file_path))

            new_active_pl.indexer.reinitialize_indexer(active_kb.name)
            new_active_pl.update_indexer_to_retriever()
            await refresh_milvus_map(milvus_name)
        else:
            new_active_pl.indexer.reinitialize_indexer()
            new_active_pl.update_indexer_to_retriever()
            add_list = active_kb.get_file_paths()
            for file in add_list:
                await add_data(DataIn(local_path=file))
            if old_active_pl:
                if old_active_pl.indexer.comp_subtype == "milvus_vector":
                    await refresh_milvus_map(milvus_name)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e)

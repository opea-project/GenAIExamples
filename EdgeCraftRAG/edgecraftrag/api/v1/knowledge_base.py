# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import re
from typing import Dict, List, Union

from edgecraftrag.api.v1.data import get_nodes_with_kb
from edgecraftrag.api_schema import DataIn, ExperienceIn, KnowledgeBaseCreateIn
from edgecraftrag.components.query_preprocess import query_search
from edgecraftrag.components.retriever import get_kbs_info
from edgecraftrag.config_repository import (
    MilvusConfigRepository,
    save_knowledge_configurations,
    save_pipeline_configurations,
)
from edgecraftrag.context import ctx
from edgecraftrag.env import (
    KNOWLEDGEBASE_FILE,
    SEARCH_CONFIG_PATH,
    SEARCH_DIR,
    UI_DIRECTORY,
)
from fastapi import FastAPI, HTTPException, status
from llama_index.core.schema import Document

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
        if not active_pl:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Please activate pipeline",
            )
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", knowledge.name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base names must begin with a letter or underscore",
            )

        if knowledge.active and knowledge.comp_type == "knowledge" and knowledge.comp_subtype == "origin_kb":
            active_pl.indexer.reinitialize_indexer(knowledge.name)
            active_pl.update_indexer_to_retriever()
        elif knowledge.active and knowledge.comp_subtype == "kbadmin_kb":
            active_pl.retriever.config_kbadmin_milvus(knowledge.name)
        kb = ctx.knowledgemgr.create_knowledge_base(knowledge)
        await save_knowledge_configurations("add", kb)
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
        if rm_kb.comp_type == "knowledge" and rm_kb.comp_subtype == "origin_kb":
            if active_kb:
                if active_kb.name == knowledge_name or active_kb.idx == knowledge_name:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Cannot delete a running knowledge base.",
                    )
            kb_file_path = rm_kb.get_file_paths()
            if kb_file_path:
                if active_pl.indexer.comp_subtype == "milvus_vector":
                    active_pl.indexer.clear_milvus_collection(knowledge_name)
                    active_pl.clear_document_cache(knowledge_name)
                    if active_kb:
                        active_pl.indexer.reinitialize_indexer(active_kb.name)
                        active_pl.update_indexer_to_retriever()
                rm_kb.clear_documents(active_pl.name)
        if rm_kb.comp_type == "experience":
            if rm_kb.experience_active:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Cannot delete a running experience knowledge base.",
                )
            else:
                rm_kb.clear_experiences()
        result = ctx.knowledgemgr.delete_knowledge_base(knowledge_name)
        await save_knowledge_configurations("delete", rm_kb)
        await save_pipeline_configurations("update", active_pl)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Switch the active knowledge base
@kb_app.patch(path="/v1/knowledge/patch")
async def update_knowledge_base(knowledge: KnowledgeBaseCreateIn):
    try:
        kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge.name)
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        if active_pl.indexer.comp_subtype == "kbadmin_indexer" and kb.comp_subtype != "kbadmin_kb":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The kbadmin pipeline must correspond to the kbadmin type kb.",
            )
        if active_pl.indexer.comp_subtype != "kbadmin_indexer" and kb.comp_subtype == "kbadmin_kb":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not kbadmin pipeline cannot active kbadmin type kb.",
            )
        if kb.comp_type == "knowledge" and kb.comp_subtype == "origin_kb":
            if active_pl.indexer.comp_subtype != "milvus_vector":
                if knowledge.active and knowledge.active != kb.active:
                    await handle_reload_data(kb, active_pl)
                elif not knowledge.active and kb.description != knowledge.description:
                    pass
            else:
                if knowledge.active and knowledge.active != kb.active:
                    current_paths = kb.file_paths
                    file_paths = active_pl.compare_file_lists(kb.name, current_paths)
                    if "del_docs" not in file_paths:
                        await handle_pipeline_change(kb, active_pl, file_paths)
                    else:
                        need_delete_document_path = file_paths["del_docs"]
                        need_add_document_path = file_paths["add_docs"]
                        active_pl.indexer.reinitialize_indexer(kb.name)
                        if need_delete_document_path:
                            for file_path in need_delete_document_path:
                                await remove_file_from_knowledge_base(kb.name, DataIn(local_path=file_path))
                        if need_add_document_path:
                            for file_path in need_add_document_path:
                                add_document = await add_file_to_knowledge_base(
                                    kb.name, DataIn(local_path=file_path), False
                                )
                                await add_document_handler(add_document)
                    active_pl.indexer.reinitialize_indexer(kb.name)
                    active_pl.update_indexer_to_retriever()
                elif not knowledge.active and kb.description != knowledge.description:
                    pass
        elif kb.comp_subtype == "kbadmin_kb":
            if knowledge.active and knowledge.active != kb.active:
                active_pl.retriever.config_kbadmin_milvus(kb.name)
        result = ctx.knowledgemgr.update_knowledge_base(knowledge)
        await save_knowledge_configurations("update", kb)
        await save_pipeline_configurations("update", active_pl)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Add a files to the knowledge base
@kb_app.post(path="/v1/knowledge/{knowledge_name}/files")
async def add_file_to_knowledge_base(knowledge_name, file_path: DataIn, only_add_file: bool = True):
    try:
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge_name)
        if kb.comp_type == "experience":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The experience type cannot perform file operations.",
            )
        if kb.comp_subtype == "kbadmin_kb" or active_pl.indexer.comp_subtype == "kbadmin_indexer":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Please proceed to the kbadmin interface to perform the operation.",
            )
        # Validate and normalize the user-provided path
        user_path = file_path.local_path
        add_document = ctx.get_file_mgr().add_files(docs=user_path)
        normalized_path = os.path.normpath(os.path.join(UI_DIRECTORY, user_path))
        if not normalized_path.startswith(UI_DIRECTORY):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path")
        if os.path.isdir(normalized_path):
            for root, _, files in os.walk(normalized_path):
                for file in files:
                    file_full_path = os.path.join(root, file)
                    if file_full_path not in kb.get_file_paths():
                        kb.add_file_path(file_full_path, add_document, active_pl.name, only_add_file)
                        active_pl.add_docs_to_list(knowledge_name, file_full_path)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"File already exists {file_full_path}",
                        )
        elif os.path.isfile(normalized_path) and normalized_path in kb.get_file_paths() and only_add_file:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"File already exists {normalized_path}",
            )
        elif os.path.isfile(normalized_path) and only_add_file:
            kb.add_file_path(normalized_path, add_document, active_pl.name, only_add_file)
            active_pl.add_docs_to_list(knowledge_name, user_path)
        elif os.path.isfile(normalized_path):
            kb.add_file_path(normalized_path, add_document, active_pl.name, only_add_file)
            active_pl.add_docs_to_list(knowledge_name, user_path)
            return add_document
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error uploading file.")

        active_kb = ctx.knowledgemgr.get_active_knowledge_base()
        if active_pl.indexer.comp_subtype == "milvus_vector":
            if knowledge_name == active_kb.name:
                await add_document_handler(add_document)
            else:
                active_pl.indexer.reinitialize_indexer(knowledge_name)
                await add_document_handler(add_document)
                active_pl.indexer.reinitialize_indexer(active_kb.name)
                active_pl.update_indexer_to_retriever()
        else:
            if active_kb:
                if active_kb.name == knowledge_name or active_kb.idx == knowledge_name:
                    await add_document_handler(add_document)
        await save_knowledge_configurations("update", kb)
        await save_pipeline_configurations("update", active_pl)
        return "File upload successfully"
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Remove a file from the knowledge base
@kb_app.delete(path="/v1/knowledge/{knowledge_name}/files")
async def remove_file_from_knowledge_base(knowledge_name, file_path: DataIn):
    try:
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge_name)
        if kb.comp_type == "experience":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The experience type cannot perform file operations.",
            )
        if kb.comp_subtype == "kbadmin_kb" or active_pl.indexer.comp_subtype == "kbadmin_indexer":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Please proceed to the kbadmin interface to perform the operation.",
            )
        document_list = kb.remove_file_path(file_path.local_path, active_pl.name)
        active_pl.del_docs_to_list(knowledge_name, file_path.local_path)
        if not document_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deleted file documents  not found",
            )
        await remove_document_handler(document_list, knowledge_name)
        await save_knowledge_configurations("update", kb)
        await save_pipeline_configurations("update", active_pl)
        return "File deleted successfully"
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@kb_app.post("/v1/experience")
def get_experience_by_id_or_question(req: ExperienceIn):
    kb = ctx.knowledgemgr.get_experience_kb()
    result = kb.get_experience_by_id_or_question(req)
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
    result = kb.update_experience(experience.idx, experience.question, experience.content)
    if not result:
        raise HTTPException(404, detail="Question_idx or question not found")
    return result


@kb_app.delete("/v1/experiences")
def delete_experience(req: ExperienceIn):
    kb = ctx.knowledgemgr.get_experience_kb()
    success = kb.delete_experience(req.idx)
    if not success:
        raise HTTPException(404, detail=f"Question {req.question} not found")
    return {"message": "Question deleted"}


@kb_app.post("/v1/multiple_experiences/check")
def check_duplicate_multiple_experiences(
    experiences: List[Dict[str, Union[str, List[str]]]],
):
    kb = ctx.knowledgemgr.get_experience_kb()
    if not kb:
        raise HTTPException(404, detail="No active experience type knowledge base")
    all_existing = kb.get_all_experience()
    existing_questions = {item["question"] for item in all_existing if "question" in item}
    new_questions = [exp["question"] for exp in experiences if "question" in exp and exp["question"]]
    duplicate_questions = [q for q in new_questions if q in existing_questions]
    if duplicate_questions:
        return {
            "code": 2001,
            "detail": "Duplicate experiences are appended OR overwritten!",
        }
    else:
        kb.add_multiple_experiences(experiences, True)
        return {
            "status": "success",
            "detail": "No duplicate experiences, added successfully",
        }


@kb_app.post("/v1/multiple_experiences/confirm")
def confirm_multiple_experiences(experiences: List[Dict[str, Union[str, List[str]]]], flag: bool):
    kb = ctx.knowledgemgr.get_experience_kb()
    try:
        if not kb:
            raise HTTPException(404, detail="No active experience type knowledge base")
        kb.add_multiple_experiences(experiences, flag)
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


@kb_app.post(path="/v1/view_sub_questions")
async def view_sub_questions(que: ExperienceIn):
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    top1_issue, sub_questions_result = await query_search(
        user_input=que.question,
        SEARCH_CONFIG_PATH=SEARCH_CONFIG_PATH,
        SEARCH_DIR=SEARCH_DIR,
        pl=active_pl,
    )
    return sub_questions_result


@kb_app.get("/v1/kbadmin/kbs_list")
def get_kbs_list():
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    try:
        if not active_pl or active_pl.indexer.comp_subtype != "kbadmin_indexer":
            return []
        CONNECTION_ARGS = {"uri": active_pl.indexer.vector_url}
        kbs_list = get_kbs_info(CONNECTION_ARGS)
        kb_names = [name for name in kbs_list.keys()]
        return kb_names
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Update knowledge base data
async def add_document_handler(all_document=None):
    if ctx.get_pipeline_mgr().get_active_pipeline() is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Please activate pipeline",
        )

    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if all_document:
        nodelist = await ctx.get_pipeline_mgr().run_data_prepare(docs=all_document)
        if active_pl.indexer.comp_subtype != "kbadmin_indexer":
            if nodelist is None or len(nodelist) == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        ctx.get_node_mgr().add_nodes(active_pl.node_parser.idx, nodelist)
        return "success update file"


# Update knowledge base data
async def remove_document_handler(document_list=None, knowledge_name: str = "default_kb"):
    if ctx.get_pipeline_mgr().get_active_pipeline() is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Please activate pipeline",
        )

    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    active_kb = ctx.get_knowledge_mgr().get_active_knowledge_base()
    ctx.get_node_mgr().del_nodes_by_np_idx(active_pl.node_parser.idx)
    if active_pl.indexer.comp_subtype == "milvus_vector":
        active_pl.indexer.reinitialize_indexer(knowledge_name)
        active_pl.indexer.delete(document_list)
        if active_kb:
            active_pl.indexer.reinitialize_indexer(active_kb.name)
            active_pl.update_indexer_to_retriever()
    elif active_kb.name == knowledge_name:
        await handle_reload_data(active_kb, active_pl)


# Restore knowledge base configuration
async def restore_knowledge_configurations():
    knowledgebase_config_repo = MilvusConfigRepository.create_connection("knowledgebase_config", 1)
    all_datas = []
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if knowledgebase_config_repo:
        all_Knowledgebases_repo = knowledgebase_config_repo.get_configs()
        for Knowledgebase_data in all_Knowledgebases_repo:
            config_json = Knowledgebase_data.get("config_json")
            all_datas.append(config_json)
    else:
        if os.path.exists(KNOWLEDGEBASE_FILE):
            with open(KNOWLEDGEBASE_FILE, "r", encoding="utf-8") as f:
                all_Knowledgebases = f.read()
            all_data = json.loads(all_Knowledgebases)
            for Knowledgebase_data in all_data:
                all_datas.append(Knowledgebase_data)
    try:
        for Knowledgebase_data in all_datas:
            Knoweldge_req = KnowledgeBaseCreateIn(**Knowledgebase_data)
            kb = ctx.knowledgemgr.create_knowledge_base(Knoweldge_req)
            if not active_pl:
                continue
            if kb.comp_type == "knowledge" and kb.comp_subtype == "origin_kb":
                if Knowledgebase_data["file_paths"]:
                    if active_pl.indexer.comp_subtype != "milvus_vector" and Knowledgebase_data["active"]:
                        await handle_reload_data(kb, active_pl)
                    elif Knowledgebase_data["active"]:
                        active_pl.indexer.reinitialize_indexer(Knowledgebase_data["name"])
                        active_pl.update_indexer_to_retriever()
                    else:
                        pass
            elif kb.comp_subtype == "kbadmin_kb":
                if Knowledgebase_data["active"]:
                    active_pl.retriever.config_kbadmin_milvus(kb.name)
    except Exception as e:
        print(f"Error load Knowledge base: {e}")


async def Synchronizing_vector_data(old_active_pl, new_active_pl):
    try:
        active_kb = ctx.knowledgemgr.get_active_knowledge_base()
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        # Determine whether it is kbadmin type
        if old_active_pl:
            if (
                old_active_pl.retriever.comp_subtype == "kbadmin_retriever"
                and new_active_pl.retriever.comp_subtype == "kbadmin_retriever"
            ):
                if active_kb:
                    if active_kb.comp_subtype == "kbadmin_kb":
                        new_active_pl.retriever.config_kbadmin_milvus(active_kb.name)
                return True
            elif old_active_pl.retriever.comp_subtype == "kbadmin_retriever":
                return True
        if not active_kb:
            return True
        if new_active_pl.retriever.comp_subtype == "kbadmin_retriever":
            if active_kb:
                if active_kb.comp_subtype == "kbadmin_kb":
                    new_active_pl.retriever.config_kbadmin_milvus(active_kb.name)
            return True
        # Perform milvus data synchronization
        if new_active_pl.indexer.comp_subtype == "milvus_vector":
            # Pipeline component state not changed
            current_paths = active_kb.file_paths
            file_paths = active_pl.compare_file_lists(active_kb.name, current_paths)
            if "del_docs" not in file_paths:
                await handle_pipeline_change(active_kb, active_pl, file_paths)
            else:
                need_delete_document_path = file_paths["del_docs"]
                need_add_document_path = file_paths["add_docs"]
                active_pl.indexer.reinitialize_indexer(active_kb.name)
                if need_delete_document_path:
                    for file_path in need_delete_document_path:
                        await remove_file_from_knowledge_base(active_kb.name, DataIn(local_path=file_path))
                if need_add_document_path:
                    for file_path in need_add_document_path:
                        add_document = await add_file_to_knowledge_base(
                            active_kb.name, DataIn(local_path=file_path), False
                        )
                        await add_document_handler(add_document)
            active_pl.indexer.reinitialize_indexer(active_kb.name)
            active_pl.update_indexer_to_retriever()
        else:
            await handle_reload_data(active_kb, active_pl)
        await save_knowledge_configurations("update", active_kb)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e)


# When the pipeline is changed, the current kb and the data of the pipeline are reconstructed
async def handle_pipeline_change(kb, pl, file_paths):
    exist_file = False
    need_add_document_path = file_paths["add_docs"]
    node_lists = await get_nodes_with_kb(kb.name)
    pl.indexer.clear_milvus_collection(kb.name)
    if need_add_document_path:
        if os.path.isfile(need_add_document_path[0]):
            kb.clear_documents(pl.name)
            exist_file = True
        pl.indexer.reinitialize_indexer(kb.name)
        for file_path in need_add_document_path:
            if exist_file:
                add_document = await add_file_to_knowledge_base(kb.name, DataIn(local_path=file_path), False)
                await add_document_handler(add_document)
            else:
                add_document = []
                document = {}
                documents_list = kb.get_all_document(file_path, pl.name)
                for document in documents_list:
                    need_add_node_list = {}
                    for node in node_lists.values():
                        if document.get("doc_id") == node.get("doc_id"):
                            need_add_node_list[node["id_"]] = node
                    docuement_text = pl.nodes_to_document(need_add_node_list)
                    document["id_"] = document.get("doc_id")
                    document["text"] = docuement_text
                    document["excluded_embed_metadata_keys"] = [
                        "file_name",
                        "file_type",
                        "file_size",
                        "creation_date",
                        "last_modified_date",
                        "last_accessed_date",
                    ]
                    document["excluded_llm_metadata_keys"] = [
                        "file_name",
                        "file_type",
                        "file_size",
                        "creation_date",
                        "last_modified_date",
                        "last_accessed_date",
                    ]
                    document["metadata"] = document.get("metadata")
                    result_document = Document.from_dict(data=document)
                    add_document.append(result_document)
                pl.add_docs_to_list(kb.name, file_path)
                await add_document_handler(add_document)


# reloading data that is not a milvus indexer
async def handle_reload_data(kb, pl):
    pl.indexer.reinitialize_indexer()
    pl.update_indexer_to_retriever()
    need_add_document_path = kb.get_file_paths()
    ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
    kb.clear_documents(pl.name)
    if need_add_document_path:
        for file_path in need_add_document_path:
            add_document = await add_file_to_knowledge_base(kb.name, DataIn(local_path=file_path), False)
            await add_document_handler(add_document)

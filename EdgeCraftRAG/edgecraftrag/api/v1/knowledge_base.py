# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import itertools
import json
import os
import re
from typing import Dict, List, Union

from edgecraftrag.api_schema import DataIn, ExperienceIn, KnowledgeBaseCreateIn
from edgecraftrag.base import (
    IndexerType,
    ModelType,
    NodeParserType,
)
from edgecraftrag.components.benchmark import Benchmark
from edgecraftrag.components.indexer import KBADMINIndexer, VectorIndexer, get_kbs_info
from edgecraftrag.components.node_parser import (
    HierarchyNodeParser,
    KBADMINParser,
    SimpleNodeParser,
    SWindowNodeParser,
    UnstructedNodeParser,
)
from edgecraftrag.components.query_preprocess import query_search
from edgecraftrag.config_repository import (
    MilvusConfigRepository,
    save_knowledge_configurations,
)
from edgecraftrag.context import ctx
from edgecraftrag.env import (
    KNOWLEDGEBASE_FILE,
    SEARCH_CONFIG_PATH,
    SEARCH_DIR,
    UI_DIRECTORY,
)
from fastapi import FastAPI, HTTPException, Query, status

kb_app = FastAPI()


# Get all knowledge bases
@kb_app.get(path="/v1/knowledge")
async def get_all_knowledge_bases():
    try:
        return ctx.knowledgemgr.get_all_knowledge_bases()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Get knowledge base files in a certain range.
@kb_app.get("/v1/knowledge/{knowledge_name}/filemap")
async def get_knowledge_base_filemap(
    knowledge_name: str, page_num: int = Query(1, ge=1), page_size: int = Query(20, ge=1)
):
    kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge_name)
    if kb and kb.file_map:
        file_map = kb.file_map
        filemap_len = len(file_map)
        start = (page_num - 1) * page_size
        end = min(start + page_size, filemap_len)
        if start >= filemap_len:
            return None
        file_map_subset = itertools.islice(file_map.items(), start, end)
        return {"file_map": dict(file_map_subset), "total": kb.calculate_totals()}
    else:
        return None


# Get the specified knowledge base.
@kb_app.get("/v1/knowledge/{knowledge_name}")
async def get_knowledge_base(knowledge_name: str):
    kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge_name)
    return kb


# Get the specified knowledge base json.
@kb_app.get("/v1/knowledge/{knowledge_name}/json")
async def get_knowledge_base_json(knowledge_name: str):
    kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge_name)
    return kb.get_knowledge_json


# Create a new knowledge base
@kb_app.post(path="/v1/knowledge")
async def create_knowledge_base(knowledge: KnowledgeBaseCreateIn):
    try:
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", knowledge.name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base names must begin with a letter or underscore",
            )
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        knowledge_json = knowledge.model_dump_json()
        kb = ctx.knowledgemgr.create_knowledge_base(knowledge, knowledge_json)
        if knowledge.comp_type == "knowledge":
            try:
                await update_kb_handler(kb, knowledge)
                if knowledge.comp_subtype == "kbadmin_kb":
                    kb.indexer.config_kbadmin_milvus(knowledge.name)
                if active_pl:
                    active_pl.update_retriever_list(ctx.knowledgemgr.get_active_knowledge_base())
            except Exception as e:
                ctx.knowledgemgr.delete_knowledge_base(knowledge.name)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        await save_knowledge_configurations("add", kb)
        return "Create knowledge base successfully"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Delete the knowledge base by name
@kb_app.delete(path="/v1/knowledge/{knowledge_name}")
async def delete_knowledge_base(knowledge_name: str):
    try:
        rm_kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge_name)
        active_kbs = ctx.knowledgemgr.get_active_knowledge_base()
        kb_is_active = True if rm_kb in active_kbs else False
        if rm_kb.comp_type == "knowledge" and rm_kb.comp_subtype == "origin_kb":
            if kb_is_active:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Cannot delete a running knowledge base, please deactivate it first.",
                )
            kb_file_path = rm_kb.get_file_paths()
            if rm_kb.indexer.comp_subtype == "milvus_vector":
                rm_kb.indexer.clear_milvus_collection(knowledge_name)
            if kb_file_path:
                rm_kb.clear_documents()
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
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@kb_app.patch(path="/v1/knowledge/patch")
async def update_knowledge_base(knowledge: KnowledgeBaseCreateIn):
    try:
        kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge.name)
        if kb is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
        kb_indexer = kb.indexer
        kb_node_parser = kb.node_parser
        if kb.comp_type == "knowledge" and kb.comp_subtype == "origin_kb":
            try:
                await update_kb_handler(kb, knowledge)
            except (ValueError, Exception) as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

            # reload data for knowledge base
            node_parser_changed = kb_node_parser != kb.node_parser
            if node_parser_changed or kb_indexer != kb.indexer:
                await handle_reload_data(kb, node_parser_changed)
        elif kb.comp_subtype == "kbadmin_kb":
            kb.indexer.config_kbadmin_milvus(kb.name)
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        result = ctx.knowledgemgr.update_knowledge_base(knowledge, active_pl)
        # Update knowledge json
        knowledge_dict = knowledge.dict()
        kb.update_knowledge_json(knowledge_dict)
        await save_knowledge_configurations("update", kb)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Add files to the knowledge base
@kb_app.post(path="/v1/knowledge/{knowledge_name}/files")
async def add_file_to_knowledge_base(knowledge_name, file_path: DataIn):
    """
    1. Parse file into Llamaindex Document and add file to filemgr
    2. Add file path to knowledge base
    3. Update nodes and vector store for knowledge base
    4. Update pipeline retriever if active knowledge base's indexer changed
    """
    try:
        kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge_name)
        prev_indexer = kb.indexer
        if kb.comp_type == "experience":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The experience type cannot perform file operations.",
            )
        if kb.comp_subtype == "kbadmin_kb" or kb.indexer.comp_subtype == "kbadmin_indexer":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Please proceed to the kbadmin interface to perform the operation.",
            )
        # Validate and normalize the user-provided path
        user_path = file_path.local_path
        kb_file_list = kb.get_file_paths()
        normalized_path = os.path.normpath(os.path.join(UI_DIRECTORY, user_path))
        if not normalized_path.startswith(UI_DIRECTORY):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path")
        if os.path.isdir(normalized_path):
            for root, _, files in os.walk(normalized_path):
                for file in files:
                    file_full_path = os.path.join(root, file)
                    if file_full_path not in kb_file_list:
                        await add_document_handler(file_full_path, kb)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"File already exists {file_full_path}",
                        )
        elif os.path.isfile(normalized_path) and normalized_path in kb.get_file_paths():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"File already exists {normalized_path}",
            )
        elif os.path.isfile(normalized_path):
            await add_document_handler(normalized_path, kb)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error uploading file.")

        # update retriever with indexer since indexer updated
        if kb.active:
            active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
            if active_pl:
                active_pl.update_retriever(kb, prev_indexer)

        await save_knowledge_configurations("update", kb)
        return "File upload successfully"
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Remove a file from the knowledge base
@kb_app.delete(path="/v1/knowledge/{knowledge_name}/files")
async def remove_file_from_knowledge_base(knowledge_name, file_path: DataIn):
    try:
        kb = ctx.knowledgemgr.get_knowledge_base_by_name_or_id(knowledge_name)
        if kb.comp_type == "experience":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The experience type cannot perform file operations.",
            )
        if kb.comp_subtype == "kbadmin_kb":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Please proceed to the kbadmin interface to perform the operation.",
            )
        prev_indexer = kb.indexer
        document_list = kb.remove_file_path(file_path.local_path)
        ctx.get_file_mgr().del_file(file_path.local_path)
        if not document_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deleted file documents not found",
            )
        await remove_document_handler(document_list, kb)
        # update retriever with indexer since indexer updated
        if kb.active:
            active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
            if active_pl:
                active_pl.update_retriever(kb, prev_indexer)

        await save_knowledge_configurations("update", kb)
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
def get_kbs_list(vector_url: str = Query(default="http://localhost:29530")):
    active_kb = ctx.knowledgemgr.get_active_knowledge_base()
    try:
        CONNECTION_ARGS = {"uri": vector_url}
        kbs_list = get_kbs_info(CONNECTION_ARGS)
        kb_names = [name for name in kbs_list.keys()]
        return kb_names
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# add knowledge file node
async def add_document_handler(file_path=None, kb=None):
    if file_path and kb:
        docs = ctx.get_file_mgr().add_files(docs=file_path)
        kb.add_file_path(file_path, docs)
        nodelist = await kb.run_node_parser(docs=docs)
        ctx.get_node_mgr().add_nodes(kb.node_parser.idx, nodelist)
        await kb.add_nodes_to_indexer(nodelist)


# remove knowledge file node
async def remove_document_handler(document_list=None, kb=None):

    if kb.indexer.comp_subtype == "milvus_vector":
        kb.indexer.reinitialize_indexer(kb.name)
        kb.indexer.delete(document_list)
        ctx.get_node_mgr().del_nodes_by_np_idx(kb.node_parser.idx)
    else:
        await handle_reload_data(kb, node_parser_changed=True)


# Restore knowledge base configuration
async def restore_knowledge_configurations():
    knowledgebase_config_repo = MilvusConfigRepository.create_connection("knowledgebase_config", 1)
    all_datas = []
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
            knowledge_json = Knoweldge_req.model_dump_json()
            kb = ctx.knowledgemgr.create_knowledge_base(Knoweldge_req, knowledge_json)
            try:
                await update_kb_handler(kb, Knoweldge_req)
            except Exception as e:
                ctx.knowledgemgr.delete_knowledge_base(Knoweldge_req.name)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
            if kb.comp_type == "knowledge" and kb.comp_subtype == "origin_kb":
                if Knowledgebase_data["file_paths"]:
                    if kb.indexer.comp_subtype == "milvus_vector":
                        kb.indexer.reinitialize_indexer(Knowledgebase_data["name"])
                    else:
                        ctx.get_file_mgr().add_files(docs=Knowledgebase_data["file_paths"])
                        await handle_reload_data(kb, node_parser_changed=True)
            elif kb.comp_subtype == "kbadmin_kb":
                kb.indexer.config_kbadmin_milvus(kb.name)
        # connect retriever with active kb's indexers
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        if active_pl:
            active_pl.update_retriever_list(ctx.knowledgemgr.get_active_knowledge_base())
    except Exception as e:
        print(f"Error load Knowledge base: {e}")


# reloading data that is not a milvus indexer
async def handle_reload_data(kb, node_parser_changed: bool = False):

    if kb.indexer and kb.indexer.comp_subtype == "milvus_vector":
        kb.indexer.clear_milvus_collection(kb.name)
    kb.indexer.reinitialize_indexer(kb.name)
    # update nodes
    if node_parser_changed:
        ctx.get_node_mgr().del_nodes_by_np_idx(kb.node_parser.idx)
        kb.update_nodes([])
        kb_file_paths = kb.get_file_paths()
        for file_path in kb_file_paths:
            docs = ctx.get_file_mgr().get_docs_by_file(file_path)
            nodelist = await kb.run_node_parser(docs=docs)
            if nodelist is None or len(nodelist) == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
            ctx.get_node_mgr().add_nodes(kb.node_parser.idx, nodelist)
    # update indexer
    await kb.update_nodes_to_indexer()


async def update_kb_handler(kb, knowledge):
    if kb.enable_benchmark:
        kb.benchmark = Benchmark(True, "")
    if knowledge.node_parser is not None and knowledge.comp_subtype != "kbadmin_kb":
        np = knowledge.node_parser
        found_parser = ctx.get_node_parser_mgr().search_parser(np)
        if found_parser is not None:
            kb.node_parser = found_parser
        else:
            match np.parser_type:
                case NodeParserType.SIMPLE:
                    kb.node_parser = SimpleNodeParser(chunk_size=np.chunk_size, chunk_overlap=np.chunk_overlap)
                case NodeParserType.HIERARCHY:
                    """
                    HierarchyNodeParser is for Auto Merging Retriever
                    (https://docs.llamaindex.ai/en/stable/examples/retrievers/auto_merging_retriever/)
                    By default, the hierarchy is:
                    1st level: chunk size 2048
                    2nd level: chunk size 512
                    3rd level: chunk size 128
                    Please set chunk size with List. e.g. chunk_size=[2048,512,128]
                    """
                    kb.node_parser = HierarchyNodeParser.from_defaults(
                        chunk_sizes=np.chunk_sizes, chunk_overlap=np.chunk_overlap
                    )
                case NodeParserType.SENTENCEWINDOW:
                    kb.node_parser = SWindowNodeParser.from_defaults(window_size=np.window_size)
                case NodeParserType.UNSTRUCTURED:
                    kb.node_parser = UnstructedNodeParser(chunk_size=np.chunk_size, chunk_overlap=np.chunk_overlap)
                case NodeParserType.KBADMINPARSER:
                    kb.node_parser = KBADMINParser()
            ctx.get_node_parser_mgr().add(kb.node_parser)
    if knowledge.indexer is not None:
        ind = knowledge.indexer
        found_indexer = (
            ctx.get_indexer_mgr().search_indexer(ind) if ind.indexer_type != IndexerType.MILVUS_VECTOR else None
        )
        if found_indexer is not None:
            kb.indexer = found_indexer
        else:
            embed_model = None
            match ind.indexer_type:
                case IndexerType.DEFAULT_VECTOR | IndexerType.FAISS_VECTOR | IndexerType.MILVUS_VECTOR:
                    if ind.embedding_model:
                        embed_model = ctx.get_model_mgr().search_model(ind.embedding_model)
                        embed_type = ind.inference_type
                        if embed_model is None:
                            if embed_type == "local":
                                ind.embedding_model.model_type = ModelType.EMBEDDING
                            elif embed_type == "vllm":
                                ind.embedding_model.model_type = ModelType.VLLM_EMBEDDING
                            embed_model = ctx.get_model_mgr().load_model(ind.embedding_model)
                            ctx.get_model_mgr().add(embed_model)
                    new_indexer = VectorIndexer(embed_model, ind.indexer_type, ind.vector_url, kb.name)
                case IndexerType.KBADMIN_INDEXER:
                    kbadmin_embedding_url = ind.embedding_url
                    KBADMIN_VECTOR_URL = ind.vector_url
                    embed_model = ind.embedding_model.model_id
                    new_indexer = KBADMINIndexer(
                        embed_model, ind.indexer_type, kbadmin_embedding_url, KBADMIN_VECTOR_URL
                    )
                case _:
                    pass
            del kb.indexer
            kb.indexer = new_indexer
            ctx.get_indexer_mgr().add(kb.indexer)
    return kb

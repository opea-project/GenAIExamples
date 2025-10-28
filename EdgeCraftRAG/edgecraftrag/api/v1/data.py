# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from edgecraftrag.api_schema import DataIn, FilesIn
from edgecraftrag.context import ctx
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from werkzeug.utils import secure_filename

data_app = FastAPI()


# Upload a text or files
@data_app.post(path="/v1/data")
async def add_data(request: DataIn, docs_name: str = None):
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    docs = []
    if request.text is not None:
        docs.extend(ctx.get_file_mgr().add_text(text=request.text))
    if request.local_path is not None:
        docs.extend(ctx.get_file_mgr().add_files(docs=request.local_path, docs_name=docs_name))

    nodelist = ctx.get_pipeline_mgr().run_data_prepare(docs=docs)
    if active_pl.indexer.comp_subtype != "kbadmin_indexer":
        if nodelist is None or len(nodelist) == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    ctx.get_node_mgr().add_nodes(active_pl.node_parser.idx, nodelist)
    return "Done"


# Reindex all files
@data_app.post(path="/v1/data/reindex")
async def redindex_data():
    pl = ctx.get_pipeline_mgr().get_active_pipeline()
    kb = ctx.get_knowledge_mgr().get_active_knowledge_base()
    if kb:
        kb_name = kb.name
        docs_name = kb_name + pl.name + str(pl.indexer.d)
    else:
        kb_name = None
        docs_name = None
    ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
    pl.indexer.reinitialize_indexer(kb_name)
    pl.update_indexer_to_retriever()

    all_docs = []
    docs_list = ctx.get_file_mgr().get_kb_files_by_name(docs_name)
    for docs_file in docs_list:
        all_docs.extend(docs_file.documents)
    nodelist = ctx.get_pipeline_mgr().run_data_prepare(docs=all_docs)
    if nodelist is not None and len(nodelist) > 0:
        ctx.get_node_mgr().add_nodes(pl.node_parser.idx, nodelist)
    return "Done"


# Upload files by a list of file_path
@data_app.post(path="/v1/data/files")
async def add_files(request: FilesIn):
    docs = []
    pl = ctx.get_pipeline_mgr().get_active_pipeline()
    kb = ctx.get_knowledge_mgr().get_active_knowledge_base()
    docs_name = kb.name + pl.name + str(pl.indexer.d)
    if request.local_paths is not None:
        docs.extend(ctx.get_file_mgr().add_files(docs=request.local_path, kb_name=docs_name))

    nodelist = ctx.get_pipeline_mgr().run_data_prepare(docs=docs)
    if nodelist is None or len(nodelist) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    ctx.get_node_mgr().add_nodes(pl.node_parser.idx, nodelist)
    return "Done"


# GET files
@data_app.get(path="/v1/data/files")
async def get_files():
    return ctx.get_file_mgr().get_all_docs()


# GET a file
@data_app.get(path="/v1/data/files/{name}")
async def get_kb_files_by_name(name):
    return ctx.get_file_mgr().get_kb_files_by_name(name)


# DELETE a file
@data_app.delete(path="/v1/data/files/{name}")
async def delete_file(kb_name, file_path):
    pl = ctx.get_pipeline_mgr().get_active_pipeline()
    docs_name = kb_name + pl.name + str(pl.indexer.d)
    if ctx.get_file_mgr().del_file(docs_name, file_path):
        # Current solution: reindexing all docs after deleting one file
        # TODO: delete the nodes related to the file
        ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
        pl.indexer.reinitialize_indexer(kb_name)
        pl.update_indexer_to_retriever()
        all_docs = ctx.get_file_mgr().get_file_by_name(docs_name)
        nodelist = ctx.get_pipeline_mgr().run_data_prepare(docs=all_docs)
        if nodelist is not None and len(nodelist) > 0:
            ctx.get_node_mgr().add_nodes(pl.node_parser.idx, nodelist)

        return "File is deleted"
    else:
        return "File not found"


# DELETE a file
@data_app.delete(path="/v1/data/all_files/{name}")
async def delete_all_file(name):
    if ctx.get_file_mgr().del_kb_file(name):
        pl = ctx.get_pipeline_mgr().get_active_pipeline()

        # Current solution: reindexing all docs after deleting one file
        # TODO: delete the nodes related to the file
        ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
        pl.indexer.reinitialize_indexer()
        pl.update_indexer_to_retriever()
        return f"File {name} is deleted"
    else:
        return f"File {name} not found"


# Upload & save a file from UI
@data_app.post(path="/v1/data/file/{file_name}")
async def upload_file(file_name: str, file: UploadFile = File(...)):
    if ctx.get_pipeline_mgr().get_active_pipeline() is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Please activate pipeline and upload the file"
        )
    try:
        # DIR for server to save files uploaded by UI
        UI_DIRECTORY = os.getenv("TMPFILE_PATH", "/home/user/ui_cache")
        UPLOAD_DIRECTORY = os.path.normpath(os.path.join(UI_DIRECTORY, file_name))
        if not UPLOAD_DIRECTORY.startswith(os.path.abspath(UI_DIRECTORY) + os.sep):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file_name: directory traversal detected"
            )
        os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
        safe_filename = file.filename
        file_path = os.path.normpath(os.path.join(UPLOAD_DIRECTORY, safe_filename))
        # Ensure file_path is within UPLOAD_DIRECTORY
        if not file_path.startswith(os.path.abspath(UPLOAD_DIRECTORY)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid uploaded file name")
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        return file_path
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload file: {str(e)}"
        )

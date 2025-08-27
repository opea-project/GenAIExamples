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
async def add_data(request: DataIn):
    docs = []
    if request.text is not None:
        docs.extend(ctx.get_file_mgr().add_text(text=request.text))
    if request.local_path is not None:
        docs.extend(ctx.get_file_mgr().add_files(docs=request.local_path))

    nodelist = ctx.get_pipeline_mgr().run_data_prepare(docs=docs)
    if nodelist is None or len(nodelist) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    pl = ctx.get_pipeline_mgr().get_active_pipeline()
    ctx.get_node_mgr().add_nodes(pl.node_parser.idx, nodelist)
    return "Done"


# Reindex all files
@data_app.post(path="/v1/data/reindex")
async def redindex_data():
    pl = ctx.get_pipeline_mgr().get_active_pipeline()

    ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
    pl.indexer.reinitialize_indexer()
    pl.update_indexer_to_retriever()

    all_docs = ctx.get_file_mgr().get_all_docs()
    nodelist = ctx.get_pipeline_mgr().run_data_prepare(docs=all_docs)
    if nodelist is not None and len(nodelist) > 0:
        ctx.get_node_mgr().add_nodes(pl.node_parser.idx, nodelist)

    return "Done"


# Upload files by a list of file_path
@data_app.post(path="/v1/data/files")
async def add_files(request: FilesIn):
    docs = []
    if request.local_paths is not None:
        docs.extend(ctx.get_file_mgr().add_files(docs=request.local_paths))

    nodelist = ctx.get_pipeline_mgr().run_data_prepare(docs=docs)
    if nodelist is None or len(nodelist) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    pl = ctx.get_pipeline_mgr().get_active_pipeline()
    ctx.get_node_mgr().add_nodes(pl.node_parser.idx, nodelist)
    return "Done"


# GET files
@data_app.get(path="/v1/data/files")
async def get_files():
    return ctx.get_file_mgr().get_files()


# GET a file
@data_app.get(path="/v1/data/files/{name}")
async def get_file_docs(name):
    return ctx.get_file_mgr().get_file_by_name_or_id(name)


# DELETE a file
@data_app.delete(path="/v1/data/files/{name}")
async def delete_file(name):
    if ctx.get_file_mgr().del_file(name):
        pl = ctx.get_pipeline_mgr().get_active_pipeline()

        # Current solution: reindexing all docs after deleting one file
        # TODO: delete the nodes related to the file
        ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
        pl.indexer.reinitialize_indexer()
        pl.update_indexer_to_retriever()

        all_docs = ctx.get_file_mgr().get_all_docs()
        nodelist = ctx.get_pipeline_mgr().run_data_prepare(docs=all_docs)
        if nodelist is not None and len(nodelist) > 0:
            ctx.get_node_mgr().add_nodes(pl.node_parser.idx, nodelist)

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

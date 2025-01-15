# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from edgecraftrag.api_schema import DataIn, FilesIn
from edgecraftrag.context import ctx
from fastapi import FastAPI

data_app = FastAPI()


# Upload a text or files
@data_app.post(path="/v1/data")
async def add_data(request: DataIn):
    nodelist = None

    docs = []
    if request.text is not None:
        docs.extend(ctx.get_file_mgr().add_text(text=request.text))
    if request.local_path is not None:
        docs.extend(ctx.get_file_mgr().add_files(docs=request.local_path))

    nodelist = ctx.get_pipeline_mgr().run_data_prepare(docs=docs)
    if nodelist is None:
        return "Error"
    pl = ctx.get_pipeline_mgr().get_active_pipeline()
    # TODO: Need bug fix, when node_parser is None
    ctx.get_node_mgr().add_nodes(pl.node_parser.idx, nodelist)
    return "Done"


# Upload files by a list of file_path
@data_app.post(path="/v1/data/files")
async def add_files(request: FilesIn):
    nodelist = None

    docs = []
    if request.local_paths is not None:
        docs.extend(ctx.get_file_mgr().add_files(docs=request.local_paths))

    nodelist = ctx.get_pipeline_mgr().run_data_prepare(docs=docs)
    if nodelist is None:
        return "Error"
    pl = ctx.get_pipeline_mgr().get_active_pipeline()
    # TODO: Need bug fix, when node_parser is None
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
        # TODO: delete the nodes related to the file
        all_docs = ctx.get_file_mgr().get_all_docs()

        nodelist = ctx.get_pipeline_mgr().run_data_update(docs=all_docs)
        if nodelist is None:
            return "Error"
        pl = ctx.get_pipeline_mgr().get_active_pipeline()
        ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
        ctx.get_node_mgr().add_nodes(pl.node_parser.idx, nodelist)
        return f"File {name} is deleted"
    else:
        return f"File {name} not found"


# UPDATE a file
@data_app.patch(path="/v1/data/files/{name}")
async def update_file(name, request: DataIn):
    # 1. Delete
    if ctx.get_file_mgr().del_file(name):
        # 2. Add
        docs = []
        if request.text is not None:
            docs.extend(ctx.get_file_mgr().add_text(text=request.text))
        if request.local_path is not None:
            docs.extend(ctx.get_file_mgr().add_files(docs=request.local_path))

        # 3. Re-run the pipeline
        # TODO: update the nodes related to the file
        all_docs = ctx.get_file_mgr().get_all_docs()
        nodelist = ctx.get_pipeline_mgr().run_data_update(docs=all_docs)
        if nodelist is None:
            return "Error"
        pl = ctx.get_pipeline_mgr().get_active_pipeline()
        ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
        ctx.get_node_mgr().add_nodes(pl.node_parser.idx, nodelist)
        return f"File {name} is updated"
    else:
        return f"File {name} not found"

from comps import register_microservice
from edgecraftrag.api_schema import DataIn, FilesIn
from edgecraftrag.context import ctx


# Upload a text or files
@register_microservice(name="opea_service@ec_rag", endpoint="/v1/data", host="0.0.0.0", port=16010, methods=['POST'])
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
@register_microservice(name="opea_service@ec_rag", endpoint="/v1/data/files", host="0.0.0.0", port=16010, methods=['POST'])
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
@register_microservice(name="opea_service@ec_rag", endpoint="/v1/data/files", host="0.0.0.0", port=16010, methods=['GET'])
async def get_files():
    return ctx.get_file_mgr().get_files()


# GET a file
@register_microservice(name="opea_service@ec_rag", endpoint="/v1/data/files/{name}", host="0.0.0.0", port=16010, methods=['GET'])
async def get_file_docs(name):
    return ctx.get_file_mgr().get_docs_by_file(name)


# DELETE a file
@register_microservice(name="opea_service@ec_rag", endpoint="/v1/data/files/{name}", host="0.0.0.0", port=16010, methods=['DELETE'])
async def delete_file(name):
    if ctx.get_file_mgr().del_file(name):
        # TODO: delete the nodes related to the file
        all_docs = ctx.get_file_mgr().get_all_docs()

        nodelist = ctx.get_pipeline_mgr().run_data_prepare(docs=all_docs)
        if nodelist is None:
            return "Error"
        pl = ctx.get_pipeline_mgr().get_active_pipeline()
        ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
        ctx.get_node_mgr().add_nodes(pl.node_parser.idx, nodelist)
        return f"File {name} is deleted"
    else:
        return f"File {name} not found"


# UPDATE a file
@register_microservice(name="opea_service@ec_rag", endpoint="/v1/data/files/{name}", host="0.0.0.0", port=16010, methods=['PATCH'])
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
        nodelist = ctx.get_pipeline_mgr().run_data_prepare(docs=all_docs)
        if nodelist is None:
            return "Error"
        pl = ctx.get_pipeline_mgr().get_active_pipeline()
        ctx.get_node_mgr().del_nodes_by_np_idx(pl.node_parser.idx)
        ctx.get_node_mgr().add_nodes(pl.node_parser.idx, nodelist)
        return f"File {name} is updated"
    else:
        return f"File {name} not found"

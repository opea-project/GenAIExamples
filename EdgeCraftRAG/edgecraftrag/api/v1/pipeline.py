# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import os
import re
import weakref
from concurrent.futures import ThreadPoolExecutor

from edgecraftrag.api.v1.knowledge_base import Synchronizing_vector_data
from edgecraftrag.api_schema import MilvusConnectRequest, PipelineCreateIn
from edgecraftrag.base import IndexerType, InferenceType, ModelType, NodeParserType, PostProcessorType, RetrieverType
from edgecraftrag.components.benchmark import Benchmark
from edgecraftrag.components.generator import QnAGenerator
from edgecraftrag.components.indexer import KBADMINIndexer, VectorIndexer
from edgecraftrag.components.node_parser import (
    HierarchyNodeParser,
    KBADMINParser,
    SimpleNodeParser,
    SWindowNodeParser,
    UnstructedNodeParser,
)
from edgecraftrag.components.postprocessor import MetadataReplaceProcessor, RerankProcessor
from edgecraftrag.components.retriever import (
    AutoMergeRetriever,
    KBadminRetriever,
    SimpleBM25Retriever,
    VectorSimRetriever,
)
from edgecraftrag.context import ctx
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from pymilvus import connections

pipeline_app = FastAPI()


# GET Pipelines
@pipeline_app.get(path="/v1/settings/pipelines")
async def get_pipelines():
    return ctx.get_pipeline_mgr().get_pipelines()


# GET Pipeline
@pipeline_app.get(path="/v1/settings/pipelines/{name}")
async def get_pipeline(name):
    return ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(name)


# GET Pipeline Json Data
@pipeline_app.get(path="/v1/settings/pipelines/{name}/json")
async def get_pipeline_json(name):
    pl = ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(name)
    if pl:
        return pl.get_pipeline_json
    else:
        return None


# GET Pipeline benchmark
@pipeline_app.get(path="/v1/settings/pipeline/benchmark")
async def get_pipeline_benchmark():
    pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if pl and pl.benchmark:
        return pl.benchmark


# GET Pipeline benchmark
@pipeline_app.get(path="/v1/settings/pipelines/{name}/benchmarks")
async def get_pipeline_benchmarks(name):
    pl = ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(name)
    if pl and pl.benchmark:
        return pl.benchmark.benchmark_data_list


# POST Pipeline
@pipeline_app.post(path="/v1/settings/pipelines")
async def add_pipeline(request: PipelineCreateIn):
    pattern = re.compile(r"^[a-zA-Z0-9_]+$")
    if not pattern.fullmatch(request.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pipeline name must consist of letters, numbers, and underscores.",
        )
    return load_pipeline(request)


# PATCH Pipeline
@pipeline_app.patch(path="/v1/settings/pipelines/{name}")
async def update_pipeline(name, request: PipelineCreateIn):
    pl = ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(name)
    if pl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if pl == active_pl:
        if request.active:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Unable to patch an active pipeline...")
    async with ctx.get_pipeline_mgr()._lock:
        try:
            update_pipeline_handler(pl, request)
            pipeline_dict = request.dict()
            pl.update_pipeline_json(pipeline_dict)
        except (ValueError, Exception) as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    save_pipeline_to_file()
    return pl


# REMOVE Pipeline
@pipeline_app.delete(path="/v1/settings/pipelines/{name}")
async def remove_pipeline(name):
    try:
        res = ctx.get_pipeline_mgr().remove_pipeline_by_name_or_id(name)
        save_pipeline_to_file()
        return res
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# IMPORT pipeline json from a file
@pipeline_app.post(path="/v1/settings/pipelines/import")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    request = json.loads(content)
    pipeline_req = PipelineCreateIn(**request)
    return load_pipeline(pipeline_req)


def load_pipeline(request):
    pl = ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(request.name)
    if pl is None:
        pipeline_json = request.model_dump_json()
        pl = ctx.get_pipeline_mgr().create_pipeline(request.name, pipeline_json)
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if pl == active_pl and request.active:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Unable to patch an active pipeline...")
    try:
        update_pipeline_handler(pl, request)
        save_pipeline_to_file()
    except (ValueError, Exception) as e:
        ctx.get_pipeline_mgr().remove_pipeline_by_name_or_id(request.name)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return pl


def update_pipeline_handler(pl, req):
    active_kb = ctx.knowledgemgr.get_active_knowledge_base()
    active_pipeline = ctx.get_pipeline_mgr().get_active_pipeline()
    kb_name = active_kb.name if active_kb else "default_kb"
    pl_change = False

    if req.node_parser is not None:
        np = req.node_parser
        pl_change = ctx.get_node_parser_mgr().search_parser_change(pl, req)
        found_parser = ctx.get_node_parser_mgr().search_parser(np)
        if found_parser is not None:
            pl.node_parser = found_parser
        else:
            match np.parser_type:
                case NodeParserType.SIMPLE:
                    pl.node_parser = SimpleNodeParser(chunk_size=np.chunk_size, chunk_overlap=np.chunk_overlap)
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
                    pl.node_parser = HierarchyNodeParser.from_defaults(
                        chunk_sizes=np.chunk_sizes, chunk_overlap=np.chunk_overlap
                    )
                case NodeParserType.SENTENCEWINDOW:
                    pl.node_parser = SWindowNodeParser.from_defaults(window_size=np.window_size)
                case NodeParserType.UNSTRUCTURED:
                    pl.node_parser = UnstructedNodeParser(chunk_size=np.chunk_size, chunk_overlap=np.chunk_overlap)
                case NodeParserType.KBADMINPARSER:
                    pl.node_parser = KBADMINParser()
            ctx.get_node_parser_mgr().add(pl.node_parser)

            pl._node_changed = True

    if req.indexer is not None:
        ind = req.indexer
        found_indexer = ctx.get_indexer_mgr().search_indexer(ind)
        if found_indexer is not None:
            pl.indexer = found_indexer
        else:
            embed_model = None
            match ind.indexer_type:
                case IndexerType.DEFAULT_VECTOR | IndexerType.FAISS_VECTOR | IndexerType.MILVUS_VECTOR:
                    if ind.embedding_model:
                        embed_model = ctx.get_model_mgr().search_model(ind.embedding_model)
                        if embed_model is None:
                            ind.embedding_model.model_type = ModelType.EMBEDDING
                            embed_model = ctx.get_model_mgr().load_model(ind.embedding_model)
                            ctx.get_model_mgr().add(embed_model)
                    # TODO: **RISK** if considering 2 pipelines with different
                    # nodes, but same indexer, what will happen?
                    pl.indexer = VectorIndexer(embed_model, ind.indexer_type, ind.vector_url, kb_name)
                case IndexerType.KBADMIN_INDEXER:
                    kbadmin_embedding_url = ind.embedding_url
                    KBADMIN_VECTOR_URL = ind.vector_url
                    embed_model = ind.embedding_model.model_id
                    pl.indexer = KBADMINIndexer(
                        embed_model, ind.indexer_type, kbadmin_embedding_url, KBADMIN_VECTOR_URL
                    )
                case _:
                    pass
            ctx.get_indexer_mgr().add(pl.indexer)
            pl._index_changed = True
            pl._index_to_retriever_updated = False
            # As indexer changed, nodes are cleared in indexer's db
            pl._node_changed = True
            if req.indexer.indexer_type == "milvus_vector":
                pl.reset_node_status()

    if req.retriever is not None:
        retr = req.retriever
        match retr.retriever_type:
            case RetrieverType.VECTORSIMILARITY:
                if pl.indexer is not None:
                    pl.retriever = VectorSimRetriever(pl.indexer, similarity_top_k=retr.retrieve_topk)
                else:
                    raise Exception("No indexer")
            case RetrieverType.AUTOMERGE:
                # AutoMergeRetriever looks at a set of leaf nodes and recursively "merges" subsets of leaf nodes that reference a parent node
                if pl.indexer is not None:
                    pl.retriever = AutoMergeRetriever(pl.indexer, similarity_top_k=retr.retrieve_topk)
                else:
                    return Exception("No indexer")
            case RetrieverType.BM25:
                if pl.indexer is not None:
                    pl.retriever = SimpleBM25Retriever(pl.indexer, similarity_top_k=retr.retrieve_topk)
                else:
                    return Exception("No indexer")
            case RetrieverType.KBADMIN_RETRIEVER:
                pl.retriever = KBadminRetriever(pl.indexer, similarity_top_k=retr.retrieve_topk)
            case _:
                pass
        # Index is updated to retriever
        pl._index_to_retriever_updated = True

    if req.postprocessor is not None:
        pp = req.postprocessor
        pl.postprocessor = []
        for processor in pp:
            match processor.processor_type:
                case PostProcessorType.RERANKER:
                    if processor.reranker_model:
                        prm = processor.reranker_model
                        reranker_model = ctx.get_model_mgr().search_model(prm)
                        if reranker_model is None:
                            prm.model_type = ModelType.RERANKER
                            reranker_model = ctx.get_model_mgr().load_model(prm)
                            ctx.get_model_mgr().add(reranker_model)
                        postprocessor = RerankProcessor(reranker_model, processor.top_n)
                        pl.postprocessor.append(postprocessor)
                    else:
                        raise Exception("No reranker model")
                case PostProcessorType.METADATAREPLACE:
                    postprocessor = MetadataReplaceProcessor(target_metadata_key="window")
                    pl.postprocessor.append(postprocessor)

    if req.generator:
        gen = req.generator
        if gen.model is None:
            raise Exception("No ChatQnA Model")
        if gen.inference_type:
            model = ctx.get_model_mgr().search_model(gen.model)
            if model is None:
                if gen.inference_type == InferenceType.VLLM:
                    gen.model.model_type = ModelType.VLLM
                else:
                    gen.model.model_type = ModelType.LLM
                if pl.enable_benchmark:
                    model, tokenizer, bench_hook = ctx.get_model_mgr().load_model_ben(gen.model)
                else:
                    model = ctx.get_model_mgr().load_model(gen.model)
                ctx.get_model_mgr().add(model)
            # Use weakref to achieve model deletion and memory release
            model_ref = weakref.ref(model)
            pl.generator = QnAGenerator(
                model_ref, gen.prompt_path, gen.inference_type, gen.vllm_endpoint, gen.prompt_content
            )
            if pl.enable_benchmark:
                if "tokenizer" not in locals() or tokenizer is None:
                    _, tokenizer, bench_hook = ctx.get_model_mgr().load_model_ben(gen.model)
                pl.benchmark = Benchmark(pl.enable_benchmark, gen.inference_type, tokenizer, bench_hook)
            else:
                pl.benchmark = Benchmark(pl.enable_benchmark, gen.inference_type)
        else:
            raise Exception("Inference Type Not Supported")

    if pl.status.active != req.active:
        ctx.get_pipeline_mgr().activate_pipeline(pl.name, req.active, ctx.get_node_mgr(), kb_name)

    # Create and set up a separate event loop to run asynchronous tasks in threads
    def run_async_task():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(Synchronizing_vector_data(active_pipeline, pl, pl_change))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Synchronization error: {e}")
        finally:
            loop.close()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_async_task)
        future.result()
    return pl


# Restore pipeline configuration
def load_pipeline_from_file():
    CONFIG_DIR = "/home/user/ui_cache/configs"
    PIPELINE_FILE = os.path.join(CONFIG_DIR, "pipeline.json")
    if os.path.exists(PIPELINE_FILE):
        with open(PIPELINE_FILE, "r", encoding="utf-8") as f:
            all_pipelines = f.read()
        try:
            all_data = json.loads(all_pipelines)
            for pipeline_data in all_data:
                one_pipelinejson = json.loads(pipeline_data)
                pipeline_req = PipelineCreateIn(**one_pipelinejson)
                load_pipeline(pipeline_req)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Configuration of the persistence pipeline
def save_pipeline_to_file():
    CONFIG_DIR = "/home/user/ui_cache/configs"
    PIPELINE_FILE = os.path.join(CONFIG_DIR, "pipeline.json")

    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        pipelines_data = ctx.get_pipeline_mgr().get_pipelines()
        all_pipeline_json = []
        for pipeline in pipelines_data:
            all_pipeline_json.append(pipeline.get_pipeline_json)
        json_str = json.dumps(all_pipeline_json, indent=2, ensure_ascii=False)
        with open(PIPELINE_FILE, "w", encoding="utf-8") as f:
            f.write(json_str)
    except Exception as e:
        print(f"Error saving pipelines: {e}")


# Detecting if milvus is connected
@pipeline_app.post(path="/v1/check/milvus")
async def check_milvus(request: MilvusConnectRequest):
    vector_url = request.vector_url
    try:
        if vector_url.startswith("http://"):
            host_port = vector_url.replace("http://", "")
        elif vector_url.startswith("https://"):
            host_port = vector_url.replace("https://", "")
        else:
            host_port = vector_url
        host, port = host_port.split(":", 1)
        connections.connect(alias="knowledge_default", host=host, port=port)

        if connections.has_connection("knowledge_default"):
            return {"status": "200", "message": "Milvus connection successful."}
        else:
            return {"status": "404", "message": "Milvus connection failed."}
    except Exception as e:
        return {"status": "404", "message": f"connection failed: {str(e)}"}

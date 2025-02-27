# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import weakref

from edgecraftrag.api_schema import PipelineCreateIn
from edgecraftrag.base import IndexerType, InferenceType, ModelType, NodeParserType, PostProcessorType, RetrieverType
from edgecraftrag.components.benchmark import Benchmark
from edgecraftrag.components.generator import QnAGenerator
from edgecraftrag.components.indexer import VectorIndexer
from edgecraftrag.components.node_parser import (
    HierarchyNodeParser,
    SimpleNodeParser,
    SWindowNodeParser,
    UnstructedNodeParser,
)
from edgecraftrag.components.postprocessor import MetadataReplaceProcessor, RerankProcessor
from edgecraftrag.components.retriever import AutoMergeRetriever, SimpleBM25Retriever, VectorSimRetriever
from edgecraftrag.context import ctx
from fastapi import FastAPI

pipeline_app = FastAPI()


# GET Pipelines
@pipeline_app.get(path="/v1/settings/pipelines")
async def get_pipelines():
    return ctx.get_pipeline_mgr().get_pipelines()


# GET Pipeline
@pipeline_app.get(path="/v1/settings/pipelines/{name}")
async def get_pipeline(name):
    return ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(name)


# GET Pipeline benchmark
@pipeline_app.get(path="/v1/settings/pipelines/{name}/benchmark")
async def get_pipeline_benchmark(name):
    pl = ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(name)
    if pl and pl.benchmark:
        return pl.benchmark


# POST Pipeline
@pipeline_app.post(path="/v1/settings/pipelines")
async def add_pipeline(request: PipelineCreateIn):
    pl = ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(request.name)
    if pl is None:
        pl = ctx.get_pipeline_mgr().create_pipeline(request.name)
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if pl == active_pl:
        if not request.active:
            pass
        else:
            return "Unable to patch an active pipeline..."
    try:
        update_pipeline_handler(pl, request)
    except ValueError as e:
        ctx.get_pipeline_mgr().remove_pipeline_by_name_or_id(request.name)
        return str(e)
    return pl


# PATCH Pipeline
@pipeline_app.patch(path="/v1/settings/pipelines/{name}")
async def update_pipeline(name, request: PipelineCreateIn):
    pl = ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(name)
    if pl is None:
        return "Pipeline not exists"
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if pl == active_pl:
        if not request.active:
            pass
        else:
            return "Unable to patch an active pipeline..."
    async with ctx.get_pipeline_mgr()._lock:
        try:
            update_pipeline_handler(pl, request)
        except ValueError as e:
            return str(e)
    return pl


# REMOVE Pipeline
@pipeline_app.delete(path="/v1/settings/pipelines/{name}")
async def remove_pipeline(name):
    return ctx.get_pipeline_mgr().remove_pipeline_by_name_or_id(name)


def update_pipeline_handler(pl, req):
    if req.node_parser is not None:
        np = req.node_parser
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
            ctx.get_node_parser_mgr().add(pl.node_parser)

    if req.indexer is not None:
        ind = req.indexer
        found_indexer = ctx.get_indexer_mgr().search_indexer(ind)
        if found_indexer is not None:
            pl.indexer = found_indexer
        else:
            embed_model = None
            if ind.embedding_model:
                embed_model = ctx.get_model_mgr().search_model(ind.embedding_model)
                if embed_model is None:
                    ind.embedding_model.model_type = ModelType.EMBEDDING
                    embed_model = ctx.get_model_mgr().load_model(ind.embedding_model)
                    ctx.get_model_mgr().add(embed_model)
            match ind.indexer_type:
                case IndexerType.DEFAULT_VECTOR | IndexerType.FAISS_VECTOR:
                    # TODO: **RISK** if considering 2 pipelines with different
                    # nodes, but same indexer, what will happen?
                    pl.indexer = VectorIndexer(embed_model, ind.indexer_type)
                case _:
                    pass
            ctx.get_indexer_mgr().add(pl.indexer)

    if req.retriever is not None:
        retr = req.retriever
        match retr.retriever_type:
            case RetrieverType.VECTORSIMILARITY:
                if pl.indexer is not None:
                    pl.retriever = VectorSimRetriever(pl.indexer, similarity_top_k=retr.retrieve_topk)
                else:
                    return "No indexer"
            case RetrieverType.AUTOMERGE:
                # AutoMergeRetriever looks at a set of leaf nodes and recursively "merges" subsets of leaf nodes that reference a parent node
                if pl.indexer is not None:
                    pl.retriever = AutoMergeRetriever(pl.indexer, similarity_top_k=retr.retrieve_topk)
                else:
                    return "No indexer"
            case RetrieverType.BM25:
                if pl.indexer is not None:
                    pl.retriever = SimpleBM25Retriever(pl.indexer, similarity_top_k=retr.retrieve_topk)
                else:
                    return "No indexer"
            case _:
                pass

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
                        return "No reranker model"
                case PostProcessorType.METADATAREPLACE:
                    postprocessor = MetadataReplaceProcessor(target_metadata_key="window")
                    pl.postprocessor.append(postprocessor)

    if req.generator:
        gen = req.generator
        if gen.model is None:
            return "No ChatQnA Model"
        if gen.inference_type:
            model = ctx.get_model_mgr().search_model(gen.model)
            if model is None:
                if gen.inference_type == InferenceType.VLLM:
                    gen.model.model_type = ModelType.VLLM
                else:
                    gen.model.model_type = ModelType.LLM
                model = ctx.get_model_mgr().load_model(gen.model)
                ctx.get_model_mgr().add(model)
            # Use weakref to achieve model deletion and memory release
            model_ref = weakref.ref(model)
            pl.generator = QnAGenerator(model_ref, gen.prompt_path, gen.inference_type)

            pl.benchmark = Benchmark(pl.enable_benchmark, gen.inference_type)
        else:
            return "Inference Type Not Supported"

    if pl.status.active != req.active:
        ctx.get_pipeline_mgr().activate_pipeline(pl.name, req.active, ctx.get_node_mgr())
    return pl

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import re
import time
import weakref

from edgecraftrag.api_schema import MilvusConnectRequest, PipelineCreateIn
from edgecraftrag.base import (
    GeneratorType,
    InferenceType,
    ModelType,
    PostProcessorType,
)
from edgecraftrag.components.benchmark import Benchmark
from edgecraftrag.components.generator import FreeChatGenerator, QnAGenerator
from edgecraftrag.components.postprocessor import MetadataReplaceProcessor, RerankProcessor

from edgecraftrag.config_repository import MilvusConfigRepository, save_pipeline_configurations
from edgecraftrag.context import ctx
from edgecraftrag.env import PIPELINE_FILE
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from pymilvus import connections

pipeline_app = FastAPI()


# GET Pipelines
@pipeline_app.get(path="/v1/settings/pipelines")
async def get_pipelines(gen_type: str = None):
    return ctx.get_pipeline_mgr().get_pipelines(gen_type)


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
        bench_res = {"pipeline_bench": pl.benchmark.benchmark_data_list, "llm_bench": pl.benchmark.llm_data_list}
        return bench_res


# POST Pipeline
@pipeline_app.post(path="/v1/settings/pipelines")
async def add_pipeline(request: PipelineCreateIn):
    pattern = re.compile(r"^[a-zA-Z0-9_]+$")
    if not pattern.fullmatch(request.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pipeline name must consist of letters, numbers, and underscores.",
        )
    pl = await load_pipeline(request)
    await save_pipeline_configurations("add", pl)
    return pl


# PATCH Pipeline
@pipeline_app.patch(path="/v1/settings/pipelines/{name}")
async def update_pipeline(name, request: PipelineCreateIn):
    pl = ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(name)
    if pl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if pl == active_pl:
        if request.active:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Unable to patch an active pipeline...",
            )
    async with ctx.get_pipeline_mgr()._lock:
        try:
            await update_pipeline_handler(pl, request)
            pipeline_dict = request.dict()
            pl.update_pipeline_json(pipeline_dict)
        except (ValueError, Exception) as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    await save_pipeline_configurations("update", pl)
    return pl


# REMOVE Pipeline
@pipeline_app.delete(path="/v1/settings/pipelines/{name}")
async def remove_pipeline(name):
    try:
        pl = ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(name)
        for _, agent in ctx.agentmgr.get_agents().items():
            if pl.idx == agent.pipeline_idx:
                raise Exception(f"Please cancel the {agent.name}'s agent associated with the current pipeline first")
        res = ctx.get_pipeline_mgr().remove_pipeline_by_name_or_id(name)
        await save_pipeline_configurations("delete", pl)
        return res
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# IMPORT pipeline json from a file
@pipeline_app.post(path="/v1/settings/pipelines/import")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    request = json.loads(content)
    pipeline_req = PipelineCreateIn(**request)
    pl = await load_pipeline(pipeline_req)
    await save_pipeline_configurations("add", pl)
    return pl


async def load_pipeline(request):
    pl = ctx.get_pipeline_mgr().get_pipeline_by_name_or_id(request.name)
    if pl is None:
        pipeline_json = request.model_dump_json()
        if request.idx is not None:
            pl = ctx.get_pipeline_mgr().create_pipeline(request, pipeline_json)
        else:
            pl = ctx.get_pipeline_mgr().create_pipeline(request.name, pipeline_json)
    active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
    if pl == active_pl and request.active:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Unable to patch an active pipeline...",
        )
    try:
        await update_pipeline_handler(pl, request)
    except (ValueError, Exception) as e:
        ctx.get_pipeline_mgr().remove_pipeline_by_name_or_id(request.name)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return pl


async def update_pipeline_handler(pl, req):

    if req.retriever is not None:
        retr = req.retriever
        pl.update_retriever_config(retr.retriever_type, retr.retrieve_topk)

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

    if req.generator is not None:
        pl.generator = []
        for gen in req.generator:
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
                if gen.generator_type == GeneratorType.CHATQNA:
                    pl.generator.append(
                        QnAGenerator(
                            model_ref, gen.prompt_path, gen.inference_type, gen.vllm_endpoint, gen.prompt_content
                        )
                    )
                elif gen.generator_type == GeneratorType.FREECHAT:
                    pl.generator.append(FreeChatGenerator(model_ref, gen.inference_type, gen.vllm_endpoint))

                if pl.enable_benchmark:
                    if "tokenizer" not in locals() or tokenizer is None:
                        _, tokenizer, bench_hook = ctx.get_model_mgr().load_model_ben(gen.model)
                    pl.benchmark = Benchmark(pl.enable_benchmark, gen.inference_type, tokenizer, bench_hook)
                else:
                    pl.benchmark = Benchmark(pl.enable_benchmark, gen.inference_type)
            else:
                raise Exception("Inference Type Not Supported")

    if pl.status.active != req.active:
        ctx.get_pipeline_mgr().activate_pipeline(pl.name, req.active, ctx.get_knowledge_mgr().get_active_knowledge_base())
    return pl


# Restore pipeline configuration
async def restore_pipeline_configurations():
    milvus_repo = MilvusConfigRepository.create_connection("pipeline_config", 20)
    all_pipelines = []
    if milvus_repo:
        time.sleep(10)
        all_pipelines_repo = milvus_repo.get_configs()
        for pipeline in all_pipelines_repo:
            all_pipelines.append(pipeline.get("config_json"))
    else:
        if os.path.exists(PIPELINE_FILE):
            with open(PIPELINE_FILE, "r", encoding="utf-8") as f:
                all_pipelines = f.read()
        if all_pipelines:
            all_pipelines = json.loads(all_pipelines)
    try:
        for pipeline_data in all_pipelines:
            pipeline_req = PipelineCreateIn(**pipeline_data)
            await load_pipeline(pipeline_req)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

import requests
from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.api_schema import RagOut
from edgecraftrag.base import GeneratorType, InferenceType
from edgecraftrag.context import ctx
from edgecraftrag.utils import chain_async_generators, serialize_contexts, serialize_node_with_score, stream_generator
from fastapi import Body, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse

chatqna_app = FastAPI()
thread_pool = ThreadPoolExecutor(max_workers=16)


# Retrieval
@chatqna_app.post(path="/v1/retrieval")
async def retrieval(request: ChatCompletionRequest):
    try:
        active_kbs = ctx.knowledgemgr.get_active_knowledge_base()
        if active_kbs:
            request.user = active_kbs
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Retrieval needs to have an active knowledgebase",
            )
        contexts = await ctx.get_pipeline_mgr().run_retrieve_postprocess(chat_request=request)
        serialized_contexts = serialize_contexts(contexts)

        ragout = RagOut(query=request.messages, contexts=serialized_contexts, response="")
        return ragout
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ChatQnA
@chatqna_app.post(path="/v1/chatqna")
async def chatqna(request: ChatCompletionRequest):
    try:
        active_pl = ctx.get_pipeline_mgr().get_active_pipeline()
        sessionid = request.user
        ctx.get_session_mgr().set_current_session(sessionid)
        experience_kb = ctx.knowledgemgr.get_active_experience()
        active_kbs = ctx.knowledgemgr.get_active_knowledge_base()
        request.user = active_kbs if active_kbs else None
        if experience_kb:
            request.tool_choice = "auto" if experience_kb.experience_active else "none"

        generator = active_pl.get_generator(GeneratorType.CHATQNA)
        inference_type = generator.inference_type if generator else "local"

        request.input = ctx.get_session_mgr().concat_history(sessionid, inference_type, request.messages)

        # Run agent if activated, otherwise, run pipeline
        if ctx.get_agent_mgr().get_active_agent():
            run_agent_gen, _ = await ctx.get_agent_mgr().run_agent(chat_request=request)
            return StreamingResponse(save_session(sessionid, run_agent_gen), media_type="text/plain")

        else:
            generator = active_pl.get_generator(GeneratorType.CHATQNA)
            if not generator:
                raise Exception("code:0000Please make sure chatqna generator is available in pipeline.")
            request.model = generator.model_id

        if request.stream:
            run_pipeline_gen, _ = await ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
            return StreamingResponse(save_session(sessionid, run_pipeline_gen), media_type="text/plain")
        else:
            ret, _ = await ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
            ctx.get_session_mgr().save_current_message(sessionid, "assistant", str(ret))
            return str(ret)

    except Exception as e:
        if "code:0000" in str(e):
            return str(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ChatQnA Error: {e}",
        )


# RAGQnA
@chatqna_app.post(path="/v1/ragqna")
async def ragqna(request: ChatCompletionRequest):
    try:
        sessionid = request.user
        experience_kb = ctx.knowledgemgr.get_active_experience()
        active_kb = ctx.knowledgemgr.get_active_knowledge_base()
        request.user = active_kb if active_kb else None
        if experience_kb:
            request.tool_choice = "auto" if experience_kb.experience_active else "none"

        def serialize_retrievals(retrievals):
            return {
                "retrievals": [
                    {
                        "step": retrieval.step,
                        "query": retrieval.query,
                        "retrieved": [serialize_node_with_score(node) for node in retrieval.retrieved],
                        "reranked": [serialize_node_with_score(node) for node in retrieval.reranked],
                    }
                    for retrieval in retrievals
                ]
            }

        if ctx.get_agent_mgr().get_active_agent():
            # Save original query string before agent mutates request.messages
            original_query = request.messages
            run_agent_gen, retrievals = await ctx.get_agent_mgr().run_agent(chat_request=request)

            if request.stream:

                async def res_gen_json():
                    async for token in run_agent_gen:
                        yield json.dumps(token, ensure_ascii=False)[1:-1]

                # Lazily serialize retrievals so it runs after res_gen_json() exhausts
                async def context_suffix_gen():
                    yield '","contexts":' + json.dumps(serialize_retrievals(retrievals)) + "}"

                query_gen = stream_generator('{"query":' + json.dumps(original_query, ensure_ascii=False) + ',"response":"')
                output_gen = chain_async_generators([query_gen, res_gen_json(), context_suffix_gen()])

                return StreamingResponse(output_gen, media_type="text/plain")
            else:
                response_tokens = []
                async for token in run_agent_gen:
                    response_tokens.append(token)
                    await asyncio.sleep(0)
                serialized_contexts = serialize_retrievals(retrievals)
                ragout = RagOut(query=original_query, contexts=serialized_contexts, response="".join(response_tokens))
                return ragout

        generator = ctx.get_pipeline_mgr().get_active_pipeline().get_generator(GeneratorType.CHATQNA)
        if generator:
            request.model = generator.model_id
        if request.stream:
            res_gen, contexts = await ctx.get_pipeline_mgr().run_pipeline(chat_request=request)

            # Escape newlines for json format as value
            async def res_gen_json():
                async for token in res_gen:
                    yield json.dumps(token, ensure_ascii=False)[1:-1]

            # Reconstruct RagOut in stream response
            query_gen = stream_generator('{"query":' + json.dumps(request.messages, ensure_ascii=False) + ',')

            s_contexts = json.dumps(serialize_contexts(contexts))
            context_gen = stream_generator('"contexts":' + s_contexts + ',"response":"')
            final_gen = stream_generator('"}')
            output_gen = chain_async_generators([query_gen, context_gen, res_gen_json(), final_gen])

            return StreamingResponse(output_gen, media_type="text/plain")
        else:
            ret, contexts = await ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
            serialized_contexts = serialize_contexts(contexts)

            ragout = RagOut(query=request.messages, contexts=serialized_contexts, response=str(ret))
            return ragout

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Detecting if vllm is connected
@chatqna_app.post(path="/v1/check/vllm")
def check_vllm(request_data: dict = Body(...)):
    try:
        server = request_data.get("server_address", "http://localhost:8086")
        model = request_data.get("model_name", "Qwen/Qwen3-8B")
        url = f"{server}/v1/completions"
        payload = {"model": model, "prompt": "Hi", "max_tokens": 16, "temperature": 0}

        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            return {"status": "200"}
        else:
            raise HTTPException(status_code=500)
    except Exception as e:
        return {"status": "500", "message": f"connection failed: {str(e)}"}


# Detecting if ovms is connected
@chatqna_app.post(path="/v1/check/ovms")
def check_ovms(request_data: dict = Body(...)):
    try:
        server = request_data.get("server_address", "http://localhost:8000").rstrip("/")
        model = request_data.get("model_name", "Qwen/Qwen3-8B")
        url = f"{server}/v3/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 16,
            "temperature": 0,
        }

        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            return {"status": "200"}
        else:
            raise HTTPException(status_code=500)
    except Exception as e:
        return {"status": "500", "message": f"connection failed: {str(e)}"}


async def save_session(sessionid, run_agent_gen):
    collected_data = []
    session_mgr = ctx.get_session_mgr()
    async for chunk in run_agent_gen:
        if chunk:
            collected_data.append(chunk)
            current_content = "".join(collected_data)
            session_mgr.update_current_message(sessionid, "assistant", current_content)
        yield chunk or ""
        await asyncio.sleep(0)
    session_mgr.save_current_message(sessionid, "assistant", current_content)

def _not_ready(reason: str):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "not_ready", "reason": reason},
    )

# Lightweight readiness check before sending a real RAG request
@chatqna_app.get(path="/v1/ready")
async def get_ready():
    pipeline = ctx.get_pipeline_mgr().get_active_pipeline()
    if pipeline is None or not pipeline.status.active:
        return _not_ready("No active pipeline")

    generator = pipeline.get_generator(GeneratorType.CHATQNA)
    if generator is not None and generator.inference_type == InferenceType.VLLM:
        try:
            response = requests.get(f"{generator.vllm_endpoint.rstrip('/')}/v1/models", timeout=2)
            response.raise_for_status()
        except Exception:
            return _not_ready("LLM backend unavailable")

    try:
        active_kbs = ctx.knowledgemgr.get_active_knowledge_base()
        if not active_kbs:
            return _not_ready("Retrieval unavailable")
        request = ChatCompletionRequest(messages="ready")
        request.user = active_kbs
        result = await ctx.get_pipeline_mgr().run_retrieve(chat_request=request)
        if result == -1:
            return _not_ready("Retrieval unavailable")
    except Exception:
        return _not_ready("Retrieval unavailable")

    return {
        "status": "ready",
        "pipeline": pipeline.name,
        "pipeline_active": pipeline.status.active,
        "llm": "ready",
        "retrieval": "ready",
    }

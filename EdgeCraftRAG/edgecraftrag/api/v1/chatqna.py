# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import List

import requests
from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.api_schema import RagOut
from edgecraftrag.context import ctx
from edgecraftrag.utils import chain_async_generators, serialize_contexts, stream_generator
from fastapi import Body, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse

chatqna_app = FastAPI()
thread_pool = ThreadPoolExecutor(max_workers=16)


# Retrieval
@chatqna_app.post(path="/v1/retrieval")
async def retrieval(request: ChatCompletionRequest):
    try:
        active_kb = ctx.knowledgemgr.get_active_knowledge_base()
        if active_kb:
            request.user = active_kb
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
        active_kb = ctx.knowledgemgr.get_active_knowledge_base()
        request.user = active_kb if active_kb else None
        if experience_kb:
            request.tool_choice = "auto" if experience_kb.experience_active else "none"

        request.input = ctx.get_session_mgr().concat_history(
            sessionid, active_pl.generator.inference_type, request.messages
        )

        # Run agent if activated, otherwise, run pipeline
        if ctx.get_agent_mgr().get_active_agent():
            run_agent_gen = await ctx.get_agent_mgr().run_agent(chat_request=request)
            return StreamingResponse(save_session(sessionid, run_agent_gen), media_type="text/plain")

        else:
            generator = active_pl.generator
            if generator:
                request.model = generator.model_id

        if request.stream:
            run_pipeline_gen, contexts = await ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
            return StreamingResponse(save_session(sessionid, run_pipeline_gen), media_type="text/plain")
        else:
            ret, contexts = await ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
            ctx.get_session_mgr().save_current_message(sessionid, "assistant", str(ret))
            return str(ret)

    except Exception as e:
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
        generator = ctx.get_pipeline_mgr().get_active_pipeline().generator
        if generator:
            request.model = generator.model_id
        if request.stream:
            res_gen, contexts = await ctx.get_pipeline_mgr().run_pipeline(chat_request=request)

            # Escape newlines for json format as value
            async def res_gen_json():
                async for token in res_gen:
                    yield token.replace("\n", "\\n")

            # Reconstruct RagOut in stream response
            query_gen = stream_generator('{"query":"' + request.messages + '",')

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

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import requests
from comps import GeneratedDoc
from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.api_schema import RagOut
from edgecraftrag.context import ctx
from edgecraftrag.utils import serialize_contexts, set_current_session
from fastapi import Body, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

chatqna_app = FastAPI()


# Retrieval
@chatqna_app.post(path="/v1/retrieval")
async def retrieval(request: ChatCompletionRequest):
    try:
        contexts = ctx.get_pipeline_mgr().run_retrieve(chat_request=request)
        serialized_contexts = serialize_contexts(contexts)

        ragout = RagOut(query=request.messages, contexts=serialized_contexts, response="")
        return ragout
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ChatQnA
@chatqna_app.post(path="/v1/chatqna")
async def chatqna(request: ChatCompletionRequest):
    try:
        sessionid = request.user
        set_current_session(sessionid)
        kb = ctx.knowledgemgr.get_active_experience()
        if kb:
            request.tool_choice = 'auto' if kb.experience_active else 'none'
        generator = ctx.get_pipeline_mgr().get_active_pipeline().generator
        if generator:
            request.model = generator.model_id
        if request.stream:
            ret, contexts = ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
            return ret
        else:
            ret, contexts = ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
            return str(ret)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# RAGQnA
@chatqna_app.post(path="/v1/ragqna")
async def ragqna(request: ChatCompletionRequest):
    try:
        res, contexts = ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
        if isinstance(res, GeneratedDoc):
            res = res.text
        elif isinstance(res, StreamingResponse):
            collected_data = []
            async for chunk in res.body_iterator:
                collected_data.append(chunk)
            res = "".join(collected_data)

        serialized_contexts = serialize_contexts(contexts)

        ragout = RagOut(query=request.messages, contexts=serialized_contexts, response=str(res))
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

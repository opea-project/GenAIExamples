# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps import GeneratedDoc
from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.api_schema import RagOut
from edgecraftrag.context import ctx
from edgecraftrag.utils import serialize_contexts, set_current_session
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

chatqna_app = FastAPI()


# Retrieval
@chatqna_app.post(path="/v1/retrieval")
async def retrieval(request: ChatCompletionRequest):
    nodeswithscore = ctx.get_pipeline_mgr().run_retrieve(chat_request=request)
    print(nodeswithscore)
    if nodeswithscore is not None:
        ret = []
        for n in nodeswithscore:
            ret.append((n.node.node_id, n.node.text, round(float(n.score), 8)))
        return ret

    return None


# ChatQnA
@chatqna_app.post(path="/v1/chatqna")
async def chatqna(request: ChatCompletionRequest):
    try:
        sessionid = request.user
        set_current_session(sessionid)
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

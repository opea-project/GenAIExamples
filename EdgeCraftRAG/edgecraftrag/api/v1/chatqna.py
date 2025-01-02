# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps import GeneratedDoc
from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.api_schema import RagOut
from edgecraftrag.context import ctx
from fastapi import FastAPI
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
            ret.append((n.node.node_id, n.node.text, n.score))
        return ret

    return "Not found"


# ChatQnA
@chatqna_app.post(path="/v1/chatqna")
async def chatqna(request: ChatCompletionRequest):
    generator = ctx.get_pipeline_mgr().get_active_pipeline().generator
    if generator:
        request.model = generator.model_id
    if request.stream:
        ret, retri_res = ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
        return ret
    else:
        ret, retri_res = ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
        return str(ret)


# RAGQnA
@chatqna_app.post(path="/v1/ragqna")
async def ragqna(request: ChatCompletionRequest):
    res, retri_res = ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
    if isinstance(res, GeneratedDoc):
        res = res.text
    elif isinstance(res, StreamingResponse):
        collected_data = []
        async for chunk in res.body_iterator:
            collected_data.append(chunk)
        res = "".join(collected_data)

    ragout = RagOut(query=request.messages, contexts=[], response=str(res))
    for n in retri_res:
        origin_text = n.node.get_text()
        ragout.contexts.append(origin_text.strip())
    return ragout

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.context import ctx
from fastapi import FastAPI

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
    if request.stream:
        return ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
    else:
        ret = ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
        return str(ret)

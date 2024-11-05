# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps import register_microservice
from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.context import ctx


# Retrieval
@register_microservice(
    name="opea_service@ec_rag", endpoint="/v1/retrieval", host="0.0.0.0", port=16010, methods=["POST"]
)
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
@register_microservice(name="opea_service@ec_rag", endpoint="/v1/chatqna", host="0.0.0.0", port=16010, methods=["POST"])
async def chatqna(request: ChatCompletionRequest):
    ret = ctx.get_pipeline_mgr().run_pipeline(chat_request=request)
    return str(ret)

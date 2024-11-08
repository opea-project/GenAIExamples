# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from comps import MicroService, ServiceOrchestrator, ServiceType

MEGA_SERVICE_HOST_IP = os.getenv("MEGA_SERVICE_HOST_IP", "127.0.0.1")
MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 16011))
PIPELINE_SERVICE_HOST_IP = os.getenv("PIPELINE_SERVICE_HOST_IP", "127.0.0.1")
PIPELINE_SERVICE_PORT = int(os.getenv("PIPELINE_SERVICE_PORT", 16010))

from comps import Gateway, MegaServiceEndpoint
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from fastapi import Request
from fastapi.responses import StreamingResponse


class EdgeCraftRagGateway(Gateway):
    def __init__(self, megaservice, host="0.0.0.0", port=16011):
        super().__init__(
            megaservice, host, port, str(MegaServiceEndpoint.CHAT_QNA), ChatCompletionRequest, ChatCompletionResponse
        )

    async def handle_request(self, request: Request):
        input = await request.json()
        result_dict, runtime_graph = await self.megaservice.schedule(initial_inputs=input)
        for node, response in result_dict.items():
            if isinstance(response, StreamingResponse):
                return response
        last_node = runtime_graph.all_leaves()[-1]
        response = result_dict[last_node]
        choices = []
        usage = UsageInfo()
        choices.append(
            ChatCompletionResponseChoice(
                index=0,
                message=ChatMessage(role="assistant", content=response),
                finish_reason="stop",
            )
        )
        return ChatCompletionResponse(model="edgecraftrag", choices=choices, usage=usage)


class EdgeCraftRagService:
    def __init__(self, host="0.0.0.0", port=16010):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        edgecraftrag = MicroService(
            name="pipeline",
            host=PIPELINE_SERVICE_HOST_IP,
            port=PIPELINE_SERVICE_PORT,
            endpoint="/v1/chatqna",
            use_remote_service=True,
            service_type=ServiceType.UNDEFINED,
        )
        self.megaservice.add(edgecraftrag)
        self.gateway = EdgeCraftRagGateway(megaservice=self.megaservice, host="0.0.0.0", port=self.port)


if __name__ == "__main__":
    edgecraftrag = EdgeCraftRagService(host=MEGA_SERVICE_HOST_IP, port=MEGA_SERVICE_PORT)
    edgecraftrag.add_remote_service()

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from comps import MicroService, ServiceOrchestrator, ServiceType

MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 16011))
PIPELINE_SERVICE_HOST_IP = os.getenv("PIPELINE_SERVICE_HOST_IP", "127.0.0.1")
PIPELINE_SERVICE_PORT = int(os.getenv("PIPELINE_SERVICE_PORT", 16010))

from comps import MegaServiceEndpoint, ServiceRoleType
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from comps.cores.proto.docarray import LLMParams
from fastapi import Request
from fastapi.responses import StreamingResponse


class EdgeCraftRagService:
    def __init__(self, host="0.0.0.0", port=16010):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.CHAT_QNA)

    def add_remote_service(self):
        edgecraftrag = MicroService(
            name="pipeline",
            host=PIPELINE_SERVICE_HOST_IP,
            port=PIPELINE_SERVICE_PORT,
            endpoint="/v1/chatqna",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        self.megaservice.add(edgecraftrag)

    async def handle_request(self, request: Request):
        input = await request.json()
        stream_opt = input.get("stream", False)
        chat_request = ChatCompletionRequest.parse_obj(input)
        parameters = LLMParams(
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            stream=stream_opt,
            chat_template=chat_request.chat_template if chat_request.chat_template else None,
        )
        result_dict, runtime_graph = await self.megaservice.schedule(initial_inputs=input, llm_parameters=parameters)
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

    def start(self):
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )
        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])
        self.service.start()


if __name__ == "__main__":
    edgecraftrag = EdgeCraftRagService(port=MEGA_SERVICE_PORT)
    edgecraftrag.add_remote_service()
    edgecraftrag.start()

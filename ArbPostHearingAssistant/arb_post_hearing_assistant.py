# Copyright (C) 2025 Zensar Technologies Private Ltd.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import json
import os
import subprocess
import uuid
from typing import List

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.mega.utils import handle_message
from comps.cores.proto.api_protocol import (
    ArbPostHearingAssistantChatCompletionRequest,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from fastapi import Request
from fastapi.responses import StreamingResponse

MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))

LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = int(os.getenv("LLM_SERVICE_PORT", 9000))


def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs):
    if self.services[cur_node].service_type == ServiceType.ARB_POST_HEARING_ASSISTANT:
        for key_to_replace in ["text", "asr_result"]:
            if key_to_replace in inputs:
                inputs["messages"] = inputs[key_to_replace]
                del inputs[key_to_replace]

        arbPostHearingAssistant_parameters = kwargs.get("arbPostHearingAssistant_parameters", None)
        if arbPostHearingAssistant_parameters:
            arbPostHearingAssistant_parameters = arbPostHearingAssistant_parameters.model_dump()
            del arbPostHearingAssistant_parameters["messages"]
            inputs.update(arbPostHearingAssistant_parameters)
        if "id" in inputs:
            del inputs["id"]
        if "max_new_tokens" in inputs:
            del inputs["max_new_tokens"]
        if "input" in inputs:
            del inputs["input"]
    return inputs


def align_outputs(self, data, *args, **kwargs):
    return data


class OpeaArbPostHearingAssistantService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        ServiceOrchestrator.align_inputs = align_inputs
        ServiceOrchestrator.align_outputs = align_outputs
        self.megaservice = ServiceOrchestrator()
        self.endpoint = "/v1/arb-post-hearing"

    def add_remote_service(self):

        arb_post_hearing_assistant = MicroService(
            name="opea_service@arb_post_hearing_assistant",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/arb-post-hearing",
            use_remote_service=True,
            service_type=ServiceType.ARB_POST_HEARING_ASSISTANT,
        )
        self.megaservice.add(arb_post_hearing_assistant)

    async def handle_request(self, request: Request):
        """Accept pure text."""
        if "application/json" in request.headers.get("content-type"):
            data = await request.json()
            chunk_size = data.get("chunk_size", -1)
            chunk_overlap = data.get("chunk_overlap", -1)
            chat_request = ArbPostHearingAssistantChatCompletionRequest.model_validate(data)
            prompt = handle_message(chat_request.messages)
            print(f"messages:{chat_request.messages}")
            print(f"prompt: {prompt}")
            initial_inputs_data = {data["type"]: prompt}
        else:
            raise ValueError(f"Unknown request type: {request.headers.get('content-type')}")

        arbPostHearingAssistant_parameters = ArbPostHearingAssistantChatCompletionRequest(
            messages=chat_request.messages,
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            model=chat_request.model if chat_request.model else None,
            language=chat_request.language if chat_request.language else "en",
            chunk_overlap=chunk_overlap,
            chunk_size=chunk_size,
        )
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs=initial_inputs_data, arbPostHearingAssistant_parameters=arbPostHearingAssistant_parameters
        )

        for node, response in result_dict.items():
            # Here it suppose the last microservice in the megaservice is LLM.
            if (
                isinstance(response, StreamingResponse)
                and node == list(self.megaservice.services.keys())[-1]
                and self.megaservice.services[node].service_type == ServiceType.ARB_POST_HEARING_ASSISTANT
            ):
                return response

        last_node = runtime_graph.all_leaves()[-1]
        response = result_dict[last_node]["text"]
        choices = []
        usage = UsageInfo()
        choices.append(
            ChatCompletionResponseChoice(
                index=0,
                message=ChatMessage(role="assistant", content=response),
                finish_reason="stop",
            )
        )
        return ChatCompletionResponse(model="arbPostHearingAssistant", choices=choices, usage=usage)

    def start(self):
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ArbPostHearingAssistantChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )
        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])
        self.service.start()


if __name__ == "__main__":
    arbPostHearingAssistant = OpeaArbPostHearingAssistantService(port=MEGA_SERVICE_PORT)
    arbPostHearingAssistant.add_remote_service()
    arbPostHearingAssistant.start()

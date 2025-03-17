# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.proto.api_protocol import (
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


class TranslationService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.TRANSLATION)

    def add_remote_service(self):
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        self.megaservice.add(llm)

    async def handle_request(self, request: Request):
        data = await request.json()
        language_from = data["language_from"]
        language_to = data["language_to"]
        source_data = data["source_data"]
        translate_type = data["translate_type"]
        if translate_type == "code":
            prompt_template = """
                ### System: Please translate the following {language_from} codes into {language_to} codes.

                ### Original codes:
                '''{language_from}

                {source_data}

                '''

                ### Translated codes:
            """
        elif translate_type == "text":
            prompt_template = """
                Translate this from {language_from} to {language_to}:

                {language_from}:
                {source_data}

                {language_to}:
            """
        else:
            raise ValueError("Invalid translate_type")
        
        prompt = prompt_template.format(
            language_from=language_from, language_to=language_to, source_data=source_data
        )
        result_dict, runtime_graph = await self.megaservice.schedule(initial_inputs={"query": prompt})
        for node, response in result_dict.items():
            # Here it suppose the last microservice in the megaservice is LLM.
            if (
                isinstance(response, StreamingResponse)
                and node == list(self.megaservice.services.keys())[-1]
                and self.megaservice.services[node].service_type == ServiceType.LLM
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
        return ChatCompletionResponse(model="translation", choices=choices, usage=usage)

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
    translation = TranslationService(port=MEGA_SERVICE_PORT)
    translation.add_remote_service()
    translation.start()

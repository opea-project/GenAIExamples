# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
import sys

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.proto.api_protocol import AudioChatCompletionRequest, ChatCompletionResponse
from comps.cores.proto.docarray import LLMParams
from fastapi import Request

MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))
ASR_SERVICE_HOST_IP = os.getenv("ASR_SERVICE_HOST_IP", "0.0.0.0")
ASR_SERVICE_PORT = int(os.getenv("ASR_SERVICE_PORT", 9099))
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = int(os.getenv("LLM_SERVICE_PORT", 9000))
TTS_SERVICE_HOST_IP = os.getenv("TTS_SERVICE_HOST_IP", "0.0.0.0")
TTS_SERVICE_PORT = int(os.getenv("TTS_SERVICE_PORT", 9088))
ANIMATION_SERVICE_HOST_IP = os.getenv("ANIMATION_SERVICE_HOST_IP", "0.0.0.0")
ANIMATION_SERVICE_PORT = int(os.getenv("ANIMATION_SERVICE_PORT", 9066))


def check_env_vars(env_var_list):
    for var in env_var_list:
        if os.getenv(var) is None:
            print(f"Error: The environment variable '{var}' is not set.")
            sys.exit(1)  # Exit the program with a non-zero status code
    print("All environment variables are set.")


class AvatarChatbotService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.AVATAR_CHATBOT)

    def add_remote_service(self):
        asr = MicroService(
            name="asr",
            host=ASR_SERVICE_HOST_IP,
            port=ASR_SERVICE_PORT,
            endpoint="/v1/audio/transcriptions",
            use_remote_service=True,
            service_type=ServiceType.ASR,
        )
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        tts = MicroService(
            name="tts",
            host=TTS_SERVICE_HOST_IP,
            port=TTS_SERVICE_PORT,
            endpoint="/v1/audio/speech",
            use_remote_service=True,
            service_type=ServiceType.TTS,
        )
        animation = MicroService(
            name="animation",
            host=ANIMATION_SERVICE_HOST_IP,
            port=ANIMATION_SERVICE_PORT,
            endpoint="/v1/animation",
            use_remote_service=True,
            service_type=ServiceType.ANIMATION,
        )
        self.megaservice.add(asr).add(llm).add(tts).add(animation)
        self.megaservice.flow_to(asr, llm)
        self.megaservice.flow_to(llm, tts)
        self.megaservice.flow_to(tts, animation)

    async def handle_request(self, request: Request):
        data = await request.json()

        chat_request = AudioChatCompletionRequest.model_validate(data)
        parameters = LLMParams(
            # relatively lower max_tokens for audio conversation
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 128,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            repetition_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 1.03,
            streaming=False,  # TODO add streaming LLM output as input to TTS
        )
        # print(parameters)

        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"byte_str": chat_request.audio}, llm_parameters=parameters
        )

        last_node = runtime_graph.all_leaves()[-1]
        response = result_dict[last_node]["video_path"]
        return response

    def start(self):
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=AudioChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )
        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])
        self.service.start()


if __name__ == "__main__":
    check_env_vars(
        [
            "MEGA_SERVICE_HOST_IP",
            "MEGA_SERVICE_PORT",
            "ASR_SERVICE_HOST_IP",
            "ASR_SERVICE_PORT",
            "LLM_SERVICE_HOST_IP",
            "LLM_SERVICE_PORT",
            "TTS_SERVICE_HOST_IP",
            "TTS_SERVICE_PORT",
            "ANIMATION_SERVICE_HOST_IP",
            "ANIMATION_SERVICE_PORT",
        ]
    )

    avatarchatbot = AvatarChatbotService(port=MEGA_SERVICE_PORT)
    avatarchatbot.add_remote_service()
    avatarchatbot.start()

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
WHISPER_SERVER_HOST_IP = os.getenv("WHISPER_SERVER_HOST_IP", "0.0.0.0")
WHISPER_SERVER_PORT = int(os.getenv("WHISPER_SERVER_PORT", 7066))
LLM_SERVER_HOST_IP = os.getenv("LLM_SERVER_HOST_IP", "0.0.0.0")
LLM_SERVER_PORT = int(os.getenv("LLM_SERVER_PORT", 3006))
SPEECHT5_SERVER_HOST_IP = os.getenv("SPEECHT5_SERVER_HOST_IP", "0.0.0.0")
SPEECHT5_SERVER_PORT = int(os.getenv("SPEECHT5_SERVER_PORT", 7055))
ANIMATION_SERVICE_HOST_IP = os.getenv("ANIMATION_SERVICE_HOST_IP", "0.0.0.0")
ANIMATION_SERVICE_PORT = int(os.getenv("ANIMATION_SERVICE_PORT", 9066))


def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs):
    if self.services[cur_node].service_type == ServiceType.LLM:
        # convert TGI/vLLM to unified OpenAI /v1/chat/completions format
        next_inputs = {}
        next_inputs["model"] = "tgi"  # specifically clarify the fake model to make the format unified
        next_inputs["messages"] = [{"role": "user", "content": inputs["asr_result"]}]
        next_inputs["max_tokens"] = llm_parameters_dict["max_tokens"]
        next_inputs["top_p"] = llm_parameters_dict["top_p"]
        next_inputs["stream"] = inputs["stream"]  # False as default
        next_inputs["frequency_penalty"] = inputs["frequency_penalty"]
        # next_inputs["presence_penalty"] = inputs["presence_penalty"]
        # next_inputs["repetition_penalty"] = inputs["repetition_penalty"]
        next_inputs["temperature"] = inputs["temperature"]
        inputs = next_inputs
    elif self.services[cur_node].service_type == ServiceType.TTS:
        next_inputs = {}
        next_inputs["text"] = inputs["choices"][0]["message"]["content"]
        next_inputs["voice"] = kwargs["voice"]
        inputs = next_inputs
    elif self.services[cur_node].service_type == ServiceType.ANIMATION:
        next_inputs = {}
        next_inputs["byte_str"] = inputs["tts_result"]
        inputs = next_inputs
    return inputs


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
        ServiceOrchestrator.align_inputs = align_inputs
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.AVATAR_CHATBOT)

    def add_remote_service(self):
        asr = MicroService(
            name="asr",
            host=WHISPER_SERVER_HOST_IP,
            port=WHISPER_SERVER_PORT,
            endpoint="/v1/asr",
            use_remote_service=True,
            service_type=ServiceType.ASR,
        )
        llm = MicroService(
            name="llm",
            host=LLM_SERVER_HOST_IP,
            port=LLM_SERVER_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        tts = MicroService(
            name="tts",
            host=SPEECHT5_SERVER_HOST_IP,
            port=SPEECHT5_SERVER_PORT,
            endpoint="/v1/tts",
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
            stream=False,  # TODO add stream LLM output as input to TTS
        )
        # print(parameters)

        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"audio": chat_request.audio},
            llm_parameters=parameters,
            voice=chat_request.voice if hasattr(chat_request, "voice") else "default",
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
            "WHISPER_SERVER_HOST_IP",
            "WHISPER_SERVER_PORT",
            "LLM_SERVER_HOST_IP",
            "LLM_SERVER_PORT",
            "SPEECHT5_SERVER_HOST_IP",
            "SPEECHT5_SERVER_PORT",
            "ANIMATION_SERVICE_HOST_IP",
            "ANIMATION_SERVICE_PORT",
        ]
    )

    avatarchatbot = AvatarChatbotService(port=MEGA_SERVICE_PORT)
    avatarchatbot.add_remote_service()
    avatarchatbot.start()

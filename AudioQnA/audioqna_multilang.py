# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import os

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.proto.api_protocol import AudioChatCompletionRequest, ChatCompletionResponse
from comps.cores.proto.docarray import LLMParams
from fastapi import Request

MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))

WHISPER_SERVER_HOST_IP = os.getenv("WHISPER_SERVER_HOST_IP", "0.0.0.0")
WHISPER_SERVER_PORT = int(os.getenv("WHISPER_SERVER_PORT", 7066))
GPT_SOVITS_SERVER_HOST_IP = os.getenv("GPT_SOVITS_SERVER_HOST_IP", "0.0.0.0")
GPT_SOVITS_SERVER_PORT = int(os.getenv("GPT_SOVITS_SERVER_PORT", 9088))
LLM_SERVER_HOST_IP = os.getenv("LLM_SERVER_HOST_IP", "0.0.0.0")
LLM_SERVER_PORT = int(os.getenv("LLM_SERVER_PORT", 8888))
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "Intel/neural-chat-7b-v3-3")


def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs):

    if self.services[cur_node].service_type == ServiceType.LLM:
        # convert TGI/vLLM to unified OpenAI /v1/chat/completions format
        next_inputs = {}
        next_inputs["model"] = LLM_MODEL_ID
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
        next_inputs["text_language"] = kwargs["tts_text_language"] if "tts_text_language" in kwargs else "zh"
        inputs = next_inputs
    return inputs


def align_outputs(self, data, cur_node, inputs, runtime_graph, llm_parameters_dict, **kwargs):
    if self.services[cur_node].service_type == ServiceType.TTS:
        audio_base64 = base64.b64encode(data).decode("utf-8")
        return {"byte_str": audio_base64}
    return data


class AudioQnAService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        ServiceOrchestrator.align_inputs = align_inputs
        ServiceOrchestrator.align_outputs = align_outputs
        self.megaservice = ServiceOrchestrator()

        self.endpoint = str(MegaServiceEndpoint.AUDIO_QNA)

    def add_remote_service(self):
        asr = MicroService(
            name="asr",
            host=WHISPER_SERVER_HOST_IP,
            port=WHISPER_SERVER_PORT,
            # endpoint="/v1/audio/transcriptions",
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
            host=GPT_SOVITS_SERVER_HOST_IP,
            port=GPT_SOVITS_SERVER_PORT,
            # endpoint="/v1/audio/speech",
            endpoint="/",
            use_remote_service=True,
            service_type=ServiceType.TTS,
        )
        self.megaservice.add(asr).add(llm).add(tts)
        self.megaservice.flow_to(asr, llm)
        self.megaservice.flow_to(llm, tts)

    async def handle_request(self, request: Request):
        data = await request.json()

        chat_request = AudioChatCompletionRequest.parse_obj(data)
        parameters = LLMParams(
            # relatively lower max_tokens for audio conversation
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 128,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            stream=False,  # TODO add stream LLM output as input to TTS
        )
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"audio": chat_request.audio}, llm_parameters=parameters
        )

        last_node = runtime_graph.all_leaves()[-1]
        response = result_dict[last_node]["byte_str"]

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
    audioqna = AudioQnAService(port=MEGA_SERVICE_PORT)
    audioqna.add_remote_service()
    audioqna.start()

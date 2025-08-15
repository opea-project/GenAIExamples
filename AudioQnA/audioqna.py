# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.proto.api_protocol import AudioChatCompletionRequest, ChatCompletionResponse
from comps.cores.proto.docarray import LLMParams
from fastapi import Request

MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))
WHISPER_SERVER_HOST_IP = os.getenv("WHISPER_SERVER_HOST_IP", "0.0.0.0")
WHISPER_SERVER_PORT = int(os.getenv("WHISPER_SERVER_PORT", 7066))
SPEECHT5_SERVER_HOST_IP = os.getenv("SPEECHT5_SERVER_HOST_IP", "0.0.0.0")
SPEECHT5_SERVER_PORT = int(os.getenv("SPEECHT5_SERVER_PORT", 7055))
LLM_SERVER_HOST_IP = os.getenv("LLM_SERVER_HOST_IP", "0.0.0.0")
LLM_SERVER_PORT = int(os.getenv("LLM_SERVER_PORT", 3006))
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "meta-llama/Meta-Llama-3-8B-Instruct")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)


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
        next_inputs["temperature"] = inputs["temperature"]
        inputs = next_inputs
    elif self.services[cur_node].service_type == ServiceType.TTS:
        next_inputs = {}
        next_inputs["text"] = inputs["text"]
        next_inputs["voice"] = kwargs["voice"]
        inputs = next_inputs
    return inputs


def align_outputs(self, data, cur_node, inputs, runtime_graph, llm_parameters_dict, **kwargs):
    next_data = {}
    if self.services[cur_node].service_type == ServiceType.LLM and not llm_parameters_dict["stream"]:
        next_data["text"] = data["choices"][0]["message"]["content"]
    else:
        next_data = data

    return next_data


def align_generator(self, gen, **kwargs):
    # OpenAI response format
    # b'data:{"id":"","object":"text_completion","created":1725530204,"model":"meta-llama/Meta-Llama-3-8B-Instruct","system_fingerprint":"2.0.1-native","choices":[{"index":0,"delta":{"role":"assistant","content":"?"},"logprobs":null,"finish_reason":null}]}\n\n'
    for line in gen:
        line = line.decode("utf-8")
        start = line.find("{")
        end = line.rfind("}") + 1

        json_str = line[start:end]
        try:
            # sometimes yield empty chunk, do a fallback here
            json_data = json.loads(json_str)
            if "ops" in json_data and "op" in json_data["ops"][0]:
                if "value" in json_data["ops"][0] and isinstance(json_data["ops"][0]["value"], str):
                    yield f"data: {repr(json_data['ops'][0]['value'].encode('utf-8'))}\n\n"
                else:
                    pass
            elif "content" in json_data["choices"][0]["delta"]:
                yield f"data: {repr(json_data['choices'][0]['delta']['content'].encode('utf-8'))}\n\n"
        except Exception as e:
            yield f"data: {repr(json_str.encode('utf-8'))}\n\n"
    yield "data: [DONE]\n\n"


class AudioQnAService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        ServiceOrchestrator.align_inputs = align_inputs
        ServiceOrchestrator.align_outputs = align_outputs
        ServiceOrchestrator.align_generator = align_generator
        self.megaservice = ServiceOrchestrator()

        self.endpoint = str(MegaServiceEndpoint.AUDIO_QNA)

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
            api_key=OPENAI_API_KEY,
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
            initial_inputs={"audio": chat_request.audio},
            llm_parameters=parameters,
            voice=chat_request.voice if hasattr(chat_request, "voice") else "default",
        )

        last_node = runtime_graph.all_leaves()[-1]
        response = result_dict[last_node]["tts_result"]

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

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import json
import os
from io import BytesIO

import requests
from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from comps.cores.proto.docarray import LLMParams
from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image

MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))
MM_EMBEDDING_SERVICE_HOST_IP = os.getenv("MM_EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
MM_EMBEDDING_PORT_MICROSERVICE = int(os.getenv("MM_EMBEDDING_PORT_MICROSERVICE", 6000))
MM_RETRIEVER_SERVICE_HOST_IP = os.getenv("MM_RETRIEVER_SERVICE_HOST_IP", "0.0.0.0")
MM_RETRIEVER_SERVICE_PORT = int(os.getenv("MM_RETRIEVER_SERVICE_PORT", 7000))
LVM_SERVICE_HOST_IP = os.getenv("LVM_SERVICE_HOST_IP", "0.0.0.0")
LVM_SERVICE_PORT = int(os.getenv("LVM_SERVICE_PORT", 9399))


class MultimodalQnAService:
    asr_port = int(os.getenv("ASR_SERVICE_PORT", 3001))
    asr_endpoint = os.getenv("ASR_SERVICE_ENDPOINT", "http://0.0.0.0:{}/v1/audio/transcriptions".format(asr_port))

    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.lvm_megaservice = ServiceOrchestrator()
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.MULTIMODAL_QNA)

    def add_remote_service(self):
        mm_embedding = MicroService(
            name="embedding",
            host=MM_EMBEDDING_SERVICE_HOST_IP,
            port=MM_EMBEDDING_PORT_MICROSERVICE,
            endpoint="/v1/embeddings",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )

        mm_retriever = MicroService(
            name="retriever",
            host=MM_RETRIEVER_SERVICE_HOST_IP,
            port=MM_RETRIEVER_SERVICE_PORT,
            endpoint="/v1/retrieval",
            use_remote_service=True,
            service_type=ServiceType.RETRIEVER,
        )
        lvm = MicroService(
            name="lvm",
            host=LVM_SERVICE_HOST_IP,
            port=LVM_SERVICE_PORT,
            endpoint="/v1/lvm",
            use_remote_service=True,
            service_type=ServiceType.LVM,
        )

        # for mmrag megaservice
        self.megaservice.add(mm_embedding).add(mm_retriever).add(lvm)
        self.megaservice.flow_to(mm_embedding, mm_retriever)
        self.megaservice.flow_to(mm_retriever, lvm)

        # for lvm megaservice
        self.lvm_megaservice.add(lvm)

    def _handle_message(self, messages):
        images = []
        audios = []
        b64_types = {}
        messages_dicts = []
        decoded_audio_input = ""
        if isinstance(messages, str):
            prompt = messages
        else:
            messages_dict = {}
            system_prompt = ""
            prompt = ""
            for message in messages:
                msg_role = message["role"]
                messages_dict = {}
                if msg_role == "system":
                    system_prompt = message["content"]
                elif msg_role == "user":
                    if type(message["content"]) == list:
                        # separate each media type and store accordingly
                        text = ""
                        text_list = [item["text"] for item in message["content"] if item["type"] == "text"]
                        text += "\n".join(text_list)
                        image_list = [
                            item["image_url"]["url"] for item in message["content"] if item["type"] == "image_url"
                        ]
                        audios = [item["audio"] for item in message["content"] if item["type"] == "audio"]
                        if audios:
                            # translate audio to text. From this point forward, audio is treated like text
                            decoded_audio_input = self.convert_audio_to_text(audios)
                            b64_types["audio"] = decoded_audio_input

                        if text and not audios and not image_list:
                            messages_dict[msg_role] = text
                        elif audios and not text and not image_list:
                            messages_dict[msg_role] = decoded_audio_input
                        else:
                            messages_dict[msg_role] = (text, decoded_audio_input, image_list)

                    else:
                        messages_dict[msg_role] = message["content"]
                    messages_dicts.append(messages_dict)
                elif msg_role == "assistant":
                    messages_dict[msg_role] = message["content"]
                    messages_dicts.append(messages_dict)
                else:
                    raise ValueError(f"Unknown role: {msg_role}")

            if system_prompt:
                prompt = system_prompt + "\n"
            for i, messages_dict in enumerate(messages_dicts):
                for role, message in messages_dict.items():
                    if isinstance(message, tuple):
                        text, decoded_audio_input, image_list = message
                        if i == 0:
                            # do not add role for the very first message.
                            # this will be added by llava_server
                            if text:
                                prompt += text + "\n"
                            elif decoded_audio_input:
                                prompt += decoded_audio_input + "\n"
                        else:
                            if text:
                                prompt += role.upper() + ": " + text + "\n"
                            elif decoded_audio_input:
                                prompt += role.upper() + ": " + decoded_audio_input + "\n"
                            else:
                                prompt += role.upper() + ":"

                        if image_list:
                            for img in image_list:
                                # URL
                                if img.startswith("http://") or img.startswith("https://"):
                                    response = requests.get(img)
                                    image = Image.open(BytesIO(response.content)).convert("RGBA")
                                    image_bytes = BytesIO()
                                    image.save(image_bytes, format="PNG")
                                    img_b64_str = base64.b64encode(image_bytes.getvalue()).decode()
                                # Local Path
                                elif os.path.exists(img):
                                    image = Image.open(img).convert("RGBA")
                                    image_bytes = BytesIO()
                                    image.save(image_bytes, format="PNG")
                                    img_b64_str = base64.b64encode(image_bytes.getvalue()).decode()
                                # Bytes
                                else:
                                    img_b64_str = img

                                images.append(img_b64_str)

                    elif isinstance(message, str):
                        if i == 0:
                            # do not add role for the very first message.
                            # this will be added by llava_server
                            if message:
                                prompt += message + "\n"
                        else:
                            if message:
                                prompt += role.upper() + ": " + message + "\n"
                            else:
                                prompt += role.upper() + ":"

        if images:
            b64_types["image"] = images

        # If the query has multiple media types, return all types
        if prompt and b64_types:
            return prompt, b64_types
        else:
            return prompt

    def convert_audio_to_text(self, audio):
        # translate audio to text by passing in base64 encoded audio to ASR
        if isinstance(audio, dict):
            input_dict = {"byte_str": audio["audio"][0]}
        else:
            input_dict = {"byte_str": audio[0]}

        response = requests.post(self.asr_endpoint, data=json.dumps(input_dict))

        if response.status_code != 200:
            return JSONResponse(
                status_code=503, content={"message": "Unable to convert audio to text. {}".format(response.text)}
            )

        response = response.json()
        return response["query"]

    async def handle_request(self, request: Request):
        data = await request.json()
        stream_opt = bool(data.get("stream", False))
        if stream_opt:
            print("[ MultimodalQnAService ] stream=True not used, this has not support streaming yet!")
            stream_opt = False
        chat_request = ChatCompletionRequest.model_validate(data)
        # Multimodal RAG QnA With Videos has not yet accepts image as input during QnA.
        num_messages = len(data["messages"]) if isinstance(data["messages"], list) else 1
        messages = self._handle_message(chat_request.messages)
        decoded_audio_input = ""

        if num_messages > 1:
            # This is a follow up query, go to LVM
            cur_megaservice = self.lvm_megaservice
            if isinstance(messages, tuple):
                prompt, b64_types = messages
                if "audio" in b64_types:
                    # for metadata storage purposes
                    decoded_audio_input = b64_types["audio"]
                if "image" in b64_types:
                    initial_inputs = {"prompt": prompt, "image": b64_types["image"][0]}
                else:
                    initial_inputs = {"prompt": prompt, "image": ""}
            else:
                prompt = messages
                initial_inputs = {"prompt": prompt, "image": ""}
        else:
            # This is the first query. Ignore image input
            cur_megaservice = self.megaservice
            if isinstance(messages, tuple):
                prompt, b64_types = messages
                if "audio" in b64_types:
                    # for metadata storage purposes
                    decoded_audio_input = b64_types["audio"]
            else:
                prompt = messages
            initial_inputs = {"text": prompt}

        parameters = LLMParams(
            max_new_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            streaming=stream_opt,
            chat_template=chat_request.chat_template if chat_request.chat_template else None,
        )
        result_dict, runtime_graph = await cur_megaservice.schedule(
            initial_inputs=initial_inputs, llm_parameters=parameters
        )
        for node, response in result_dict.items():
            # the last microservice in this megaservice is LVM.
            # checking if LVM returns StreamingResponse
            # Currently, LVM with LLAVA has not yet supported streaming.
            # @TODO: Will need to test this once LVM with LLAVA supports streaming
            if (
                isinstance(response, StreamingResponse)
                and node == runtime_graph.all_leaves()[-1]
                and self.megaservice.services[node].service_type == ServiceType.LVM
            ):
                return response
        last_node = runtime_graph.all_leaves()[-1]

        if "text" in result_dict[last_node].keys():
            response = result_dict[last_node]["text"]
        else:
            # text is not in response message
            # something wrong, for example due to empty retrieval results
            if "detail" in result_dict[last_node].keys():
                response = result_dict[last_node]["detail"]
            else:
                response = "The server failed to generate an answer to your query!"
        if "metadata" in result_dict[last_node].keys():
            # from retrieval results
            metadata = result_dict[last_node]["metadata"]
            if decoded_audio_input:
                metadata["audio"] = decoded_audio_input
        else:
            # follow-up question, no retrieval
            if decoded_audio_input:
                metadata = {"audio": decoded_audio_input}
            else:
                metadata = None

        choices = []
        usage = UsageInfo()
        choices.append(
            ChatCompletionResponseChoice(
                index=0,
                message=ChatMessage(role="assistant", content=response),
                finish_reason="stop",
                metadata=metadata,
            )
        )
        return ChatCompletionResponse(model="multimodalqna", choices=choices, usage=usage)

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
    mmragwithvideos = MultimodalQnAService(port=MEGA_SERVICE_PORT)
    mmragwithvideos.add_remote_service()
    mmragwithvideos.start()

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import os
from io import BytesIO

import requests
from comps import Gateway, MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceType
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
from PIL import Image

MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))
MM_EMBEDDING_SERVICE_HOST_IP = os.getenv("MM_EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
MM_EMBEDDING_PORT_MICROSERVICE = int(os.getenv("MM_EMBEDDING_PORT_MICROSERVICE", 6000))
MM_RETRIEVER_SERVICE_HOST_IP = os.getenv("MM_RETRIEVER_SERVICE_HOST_IP", "0.0.0.0")
MM_RETRIEVER_SERVICE_PORT = int(os.getenv("MM_RETRIEVER_SERVICE_PORT", 7000))
LVM_SERVICE_HOST_IP = os.getenv("LVM_SERVICE_HOST_IP", "0.0.0.0")
LVM_SERVICE_PORT = int(os.getenv("LVM_SERVICE_PORT", 9399))


class MultimodalQnAService(Gateway):
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.lvm_megaservice = ServiceOrchestrator()
        self.megaservice = ServiceOrchestrator()

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
            endpoint="/v1/multimodal_retrieval",
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

    # this overrides _handle_message method of Gateway
    def _handle_message(self, messages):
        images = []
        messages_dicts = []
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
                        text = ""
                        text_list = [item["text"] for item in message["content"] if item["type"] == "text"]
                        text += "\n".join(text_list)
                        image_list = [
                            item["image_url"]["url"] for item in message["content"] if item["type"] == "image_url"
                        ]
                        if image_list:
                            messages_dict[msg_role] = (text, image_list)
                        else:
                            messages_dict[msg_role] = text
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
            for messages_dict in messages_dicts:
                for i, (role, message) in enumerate(messages_dict.items()):
                    if isinstance(message, tuple):
                        text, image_list = message
                        if i == 0:
                            # do not add role for the very first message.
                            # this will be added by llava_server
                            if text:
                                prompt += text + "\n"
                        else:
                            if text:
                                prompt += role.upper() + ": " + text + "\n"
                            else:
                                prompt += role.upper() + ":"
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
                    else:
                        if i == 0:
                            # do not add role for the very first message.
                            # this will be added by llava_server
                            if message:
                                prompt += role.upper() + ": " + message + "\n"
                        else:
                            if message:
                                prompt += role.upper() + ": " + message + "\n"
                            else:
                                prompt += role.upper() + ":"
        if images:
            return prompt, images
        else:
            return prompt

    async def handle_request(self, request: Request):
        data = await request.json()
        stream_opt = bool(data.get("stream", False))
        if stream_opt:
            print("[ MultimodalQnAService ] stream=True not used, this has not support streaming yet!")
            stream_opt = False
        chat_request = ChatCompletionRequest.model_validate(data)
        # Multimodal RAG QnA With Videos has not yet accepts image as input during QnA.
        prompt_and_image = self._handle_message(chat_request.messages)
        if isinstance(prompt_and_image, tuple):
            # print(f"This request include image, thus it is a follow-up query. Using lvm megaservice")
            prompt, images = prompt_and_image
            cur_megaservice = self.lvm_megaservice
            initial_inputs = {"prompt": prompt, "image": images[0]}
        else:
            # print(f"This is the first query, requiring multimodal retrieval. Using multimodal rag megaservice")
            prompt = prompt_and_image
            cur_megaservice = self.megaservice
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
            # text in not response message
            # something wrong, for example due to empty retrieval results
            if "detail" in result_dict[last_node].keys():
                response = result_dict[last_node]["detail"]
            else:
                response = "The server fail to generate answer to your query!"
        if "metadata" in result_dict[last_node].keys():
            # from retrieval results
            metadata = result_dict[last_node]["metadata"]
        else:
            # follow-up question, no retrieval
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
        super().__init__(
            megaservice=self.megaservice,
            host=self.host,
            port=self.port,
            endpoint=str(MegaServiceEndpoint.MULTIMODAL_QNA),
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )


if __name__ == "__main__":
    mmragwithvideos = MultimodalQnAService(port=MEGA_SERVICE_PORT)
    mmragwithvideos.add_remote_service()
    mmragwithvideos.start()

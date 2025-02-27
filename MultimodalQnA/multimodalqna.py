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
from comps.cores.proto.docarray import ImageDoc, LLMParams, TextDoc, TextImageDoc
from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image

MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))
MM_EMBEDDING_SERVICE_HOST_IP = os.getenv("MM_EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
MM_EMBEDDING_PORT_MICROSERVICE = int(os.getenv("MM_EMBEDDING_PORT_MICROSERVICE", 6000))
MM_RETRIEVER_SERVICE_HOST_IP = os.getenv("MM_RETRIEVER_SERVICE_HOST_IP", "0.0.0.0")
MM_RETRIEVER_SERVICE_PORT = int(os.getenv("MM_RETRIEVER_SERVICE_PORT", 7000))
LVM_SERVICE_HOST_IP = os.getenv("LVM_SERVICE_HOST_IP", "0.0.0.0")
LVM_SERVICE_PORT = int(os.getenv("LVM_PORT", 9399))
WHISPER_PORT = int(os.getenv("WHISPER_PORT", 7066))
WHISPER_SERVER_ENDPOINT = os.getenv("WHISPER_SERVER_ENDPOINT", "http://0.0.0.0:$WHISPER_PORT/v1/asr")


def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs):
    if self.services[cur_node].service_type == ServiceType.EMBEDDING:
        if "text" in inputs:
            input_text = inputs["text"]["text"] if isinstance(inputs["text"], dict) else inputs["text"]
        if "image" in inputs:
            input_image = inputs["image"]["base64_image"] if isinstance(inputs["image"], dict) else inputs["image"]
        if "text" in inputs and "image" in inputs:
            text_doc = TextDoc(text=input_text)
            image_doc = ImageDoc(base64_image=input_image)
            inputs = TextImageDoc(text=text_doc, image=image_doc).dict()
        elif "image" in inputs:
            inputs = ImageDoc(base64_image=input_image).dict()
        elif "text" in inputs:
            inputs = TextDoc(text=input_text).dict()
    return inputs


class MultimodalQnAService:

    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self._role_labels = self._get_role_labels()
        ServiceOrchestrator.align_inputs = align_inputs
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

    def _get_role_labels(self):
        """Returns a dictionary of role labels that are used in the chat prompt based on the LVM_MODEL_ID
        environment variable.

        The function defines the role labels used by the llava-1.5, llava-v1.6-vicuna,
        llava-v1.6-mistral, and llava-interleave models, and then defaults to use "USER:" and "ASSISTANT:" if the
        LVM_MODEL_ID is not one of those.
        """
        lvm_model = os.getenv("LVM_MODEL_ID", "")

        # Default to labels used by llava-1.5 and llava-v1.6-vicuna models
        role_labels = {"user": "USER:", "assistant": "ASSISTANT:"}

        if "llava-interleave" in lvm_model:
            role_labels["user"] = "<|im_start|>user"
            role_labels["assistant"] = "<|im_end|><|im_start|>assistant"
        elif "llava-v1.6-mistral" in lvm_model:
            role_labels["user"] = "[INST]"
            role_labels["assistant"] = " [/INST]"
        elif "llava-1.5" not in lvm_model and "llava-v1.6-vicuna" not in lvm_model:
            print(f"[ MultimodalQnAGateway ] Using default role labels for prompt formatting: {role_labels}")

        return role_labels

    # this overrides _handle_message method of Gateway
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
            role_label_dict = self._role_labels
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
                        # Remove empty items from the image list
                        image_list = [x for x in image_list if x]
                        # Add image indicators within the conversation
                        image_tags = "<image>\n" * len(image_list)
                        if i == 0:
                            # do not add role for the very first message.
                            # this will be added by llava_server
                            if text:
                                prompt += image_tags + text + "\n"
                            elif decoded_audio_input:
                                prompt += image_tags + decoded_audio_input + "\n"
                        else:
                            if text:
                                prompt += role_label_dict[role] + " " + image_tags + text + "\n"
                            elif decoded_audio_input:
                                prompt += role_label_dict[role] + " " + image_tags + decoded_audio_input + "\n"
                            else:
                                prompt += role_label_dict[role] + " " + image_tags

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
                                prompt += role_label_dict[role] + " " + message + "\n"
                            else:
                                prompt += role_label_dict[role]

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
            input_dict = {"audio": audio["audio"][0]}
        else:
            input_dict = {"audio": audio[0]}

        response = requests.post(WHISPER_SERVER_ENDPOINT, data=json.dumps(input_dict))

        if response.status_code != 200:
            return JSONResponse(
                status_code=503, content={"message": "Unable to convert audio to text. {}".format(response.text)}
            )

        response = response.json()
        return response["asr_result"]

    async def handle_request(self, request: Request):
        """MultimodalQnA accepts input queries as text, images, and/or audio.

        The messages in the request can be a single
        message (which would be assumed to be a first query from the user) or back and forth conversation between the
        user and the assistant.
        Audio queries are converted to text before being sent to the megaservice and the translated text is returned
        as part of the metadata in the response.
        First queries are sent to the full Multimodal megaserivce, which includes using the embedding microservice and
        retriever, in order to get relevant information from the vector store to send to the LVM along with the user's
        query. Follow up queries are sent directly to the LVM without searching for more similar information from the
        vector store.
        """
        data = await request.json()
        stream_opt = bool(data.get("stream", False))
        if stream_opt:
            print("[ MultimodalQnAService ] stream=True not used, this has not support stream yet!")
            stream_opt = False
        chat_request = ChatCompletionRequest.model_validate(data)
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
                    initial_inputs = {"prompt": prompt, "image": b64_types["image"]}
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
                initial_inputs = {"text": prompt}
                if "audio" in b64_types:
                    # for metadata storage purposes
                    decoded_audio_input = b64_types["audio"]
                if "image" in b64_types and len(b64_types["image"]) > 0:
                    # Format initial inputs to match TextImageDoc
                    initial_inputs["text"] = {"text": prompt}
                    initial_inputs["image"] = {"base64_image": b64_types["image"][0]}
            else:
                initial_inputs = {"text": messages}

        parameters = LLMParams(
            max_new_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            stream=stream_opt,
            chat_template=chat_request.chat_template if chat_request.chat_template else None,
        )
        result_dict, runtime_graph = await cur_megaservice.schedule(
            initial_inputs=initial_inputs, llm_parameters=parameters
        )
        for node, response in result_dict.items():
            # the last microservice in this megaservice is LVM.
            # checking if LVM returns StreamingResponse
            # Currently, LVM with LLAVA has not yet supported stream.
            # @TODO: Will need to test this once LVM with LLAVA supports stream
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

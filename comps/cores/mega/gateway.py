# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import os
from io import BytesIO
from typing import Union

import requests
from fastapi import Request
from fastapi.responses import StreamingResponse
from PIL import Image

from ..proto.api_protocol import (
    AudioChatCompletionRequest,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    EmbeddingRequest,
    UsageInfo,
)
from ..proto.docarray import LLMParams, LLMParamsDoc, RerankedDoc, RerankerParms, RetrieverParms, TextDoc
from .constants import MegaServiceEndpoint, ServiceRoleType, ServiceType
from .micro_service import MicroService


class Gateway:
    def __init__(
        self,
        megaservice,
        host="0.0.0.0",
        port=8888,
        endpoint=str(MegaServiceEndpoint.CHAT_QNA),
        input_datatype=ChatCompletionRequest,
        output_datatype=ChatCompletionResponse,
    ):
        self.megaservice = megaservice
        self.host = host
        self.port = port
        self.endpoint = endpoint
        self.input_datatype = input_datatype
        self.output_datatype = output_datatype
        self.service = MicroService(
            service_role=ServiceRoleType.MEGASERVICE,
            service_type=ServiceType.GATEWAY,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=self.input_datatype,
            output_datatype=self.output_datatype,
        )
        self.define_routes()
        self.service.start()

    def define_routes(self):
        self.service.app.router.add_api_route(self.endpoint, self.handle_request, methods=["POST"])
        self.service.app.router.add_api_route(str(MegaServiceEndpoint.LIST_SERVICE), self.list_service, methods=["GET"])
        self.service.app.router.add_api_route(
            str(MegaServiceEndpoint.LIST_PARAMETERS), self.list_parameter, methods=["GET"]
        )

    def add_route(self, endpoint, handler, methods=["POST"]):
        self.service.app.router.add_api_route(endpoint, handler, methods=methods)

    def stop(self):
        self.service.stop()

    async def handle_request(self, request: Request):
        raise NotImplementedError("Subclasses must implement this method")

    def list_service(self):
        response = {}
        for node in self.all_leaves():
            response = {self.services[node].description: self.services[node].endpoint_path}
        return response

    def list_parameter(self):
        pass

    def _handle_message(self, messages):
        images = []
        if isinstance(messages, str):
            prompt = messages
        else:
            messages_dict = {}
            system_prompt = ""
            prompt = ""
            for message in messages:
                msg_role = message["role"]
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
                elif msg_role == "assistant":
                    messages_dict[msg_role] = message["content"]
                else:
                    raise ValueError(f"Unknown role: {msg_role}")

            if system_prompt:
                prompt = system_prompt + "\n"
            for role, message in messages_dict.items():
                if isinstance(message, tuple):
                    text, image_list = message
                    if text:
                        prompt += role + ": " + text + "\n"
                    else:
                        prompt += role + ":"
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
                    if message:
                        prompt += role + ": " + message + "\n"
                    else:
                        prompt += role + ":"
        if images:
            return prompt, images
        else:
            return prompt


class ChatQnAGateway(Gateway):
    def __init__(self, megaservice, host="0.0.0.0", port=8888):
        super().__init__(
            megaservice, host, port, str(MegaServiceEndpoint.CHAT_QNA), ChatCompletionRequest, ChatCompletionResponse
        )

    async def handle_request(self, request: Request):
        data = await request.json()
        stream_opt = data.get("stream", True)
        chat_request = ChatCompletionRequest.parse_obj(data)
        prompt = self._handle_message(chat_request.messages)
        parameters = LLMParams(
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            streaming=stream_opt,
            chat_template=chat_request.chat_template if chat_request.chat_template else None,
        )
        retriever_parameters = RetrieverParms(
            search_type=chat_request.search_type if chat_request.search_type else "similarity",
            k=chat_request.k if chat_request.k else 4,
            distance_threshold=chat_request.distance_threshold if chat_request.distance_threshold else None,
            fetch_k=chat_request.fetch_k if chat_request.fetch_k else 20,
            lambda_mult=chat_request.lambda_mult if chat_request.lambda_mult else 0.5,
            score_threshold=chat_request.score_threshold if chat_request.score_threshold else 0.2,
        )
        reranker_parameters = RerankerParms(
            top_n=chat_request.top_n if chat_request.top_n else 1,
        )
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"text": prompt},
            llm_parameters=parameters,
            retriever_parameters=retriever_parameters,
            reranker_parameters=reranker_parameters,
        )
        for node, response in result_dict.items():
            if isinstance(response, StreamingResponse):
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
        return ChatCompletionResponse(model="chatqna", choices=choices, usage=usage)


class CodeGenGateway(Gateway):
    def __init__(self, megaservice, host="0.0.0.0", port=8888):
        super().__init__(
            megaservice, host, port, str(MegaServiceEndpoint.CODE_GEN), ChatCompletionRequest, ChatCompletionResponse
        )

    async def handle_request(self, request: Request):
        data = await request.json()
        stream_opt = data.get("stream", True)
        chat_request = ChatCompletionRequest.parse_obj(data)
        prompt = self._handle_message(chat_request.messages)
        parameters = LLMParams(
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            streaming=stream_opt,
        )
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"query": prompt}, llm_parameters=parameters
        )
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
        return ChatCompletionResponse(model="codegen", choices=choices, usage=usage)


class CodeTransGateway(Gateway):
    def __init__(self, megaservice, host="0.0.0.0", port=8888):
        super().__init__(
            megaservice, host, port, str(MegaServiceEndpoint.CODE_TRANS), ChatCompletionRequest, ChatCompletionResponse
        )

    async def handle_request(self, request: Request):
        data = await request.json()
        language_from = data["language_from"]
        language_to = data["language_to"]
        source_code = data["source_code"]
        prompt_template = """
            ### System: Please translate the following {language_from} codes into {language_to} codes.

            ### Original codes:
            '''{language_from}

            {source_code}

            '''

            ### Translated codes:
        """
        prompt = prompt_template.format(language_from=language_from, language_to=language_to, source_code=source_code)
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
        return ChatCompletionResponse(model="codetrans", choices=choices, usage=usage)


class TranslationGateway(Gateway):
    def __init__(self, megaservice, host="0.0.0.0", port=8888):
        super().__init__(
            megaservice, host, port, str(MegaServiceEndpoint.TRANSLATION), ChatCompletionRequest, ChatCompletionResponse
        )

    async def handle_request(self, request: Request):
        data = await request.json()
        language_from = data["language_from"]
        language_to = data["language_to"]
        source_language = data["source_language"]
        prompt_template = """
            Translate this from {language_from} to {language_to}:

            {language_from}:
            {source_language}

            {language_to}:
        """
        prompt = prompt_template.format(
            language_from=language_from, language_to=language_to, source_language=source_language
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


class DocSumGateway(Gateway):
    def __init__(self, megaservice, host="0.0.0.0", port=8888):
        super().__init__(
            megaservice, host, port, str(MegaServiceEndpoint.DOC_SUMMARY), ChatCompletionRequest, ChatCompletionResponse
        )

    async def handle_request(self, request: Request):
        data = await request.json()
        stream_opt = data.get("stream", True)
        chat_request = ChatCompletionRequest.parse_obj(data)
        prompt = self._handle_message(chat_request.messages)
        parameters = LLMParams(
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            streaming=stream_opt,
        )
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"query": prompt}, llm_parameters=parameters
        )
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
        return ChatCompletionResponse(model="docsum", choices=choices, usage=usage)


class AudioQnAGateway(Gateway):
    def __init__(self, megaservice, host="0.0.0.0", port=8888):
        super().__init__(
            megaservice,
            host,
            port,
            str(MegaServiceEndpoint.AUDIO_QNA),
            AudioChatCompletionRequest,
            ChatCompletionResponse,
        )

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
            streaming=False,  # TODO add streaming LLM output as input to TTS
        )
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"byte_str": chat_request.audio}, llm_parameters=parameters
        )

        last_node = runtime_graph.all_leaves()[-1]
        response = result_dict[last_node]["byte_str"]

        return response


class SearchQnAGateway(Gateway):
    def __init__(self, megaservice, host="0.0.0.0", port=8888):
        super().__init__(
            megaservice, host, port, str(MegaServiceEndpoint.SEARCH_QNA), ChatCompletionRequest, ChatCompletionResponse
        )

    async def handle_request(self, request: Request):
        data = await request.json()
        stream_opt = data.get("stream", True)
        chat_request = ChatCompletionRequest.parse_obj(data)
        prompt = self._handle_message(chat_request.messages)
        parameters = LLMParams(
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            streaming=stream_opt,
        )
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"text": prompt}, llm_parameters=parameters
        )
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
        return ChatCompletionResponse(model="searchqna", choices=choices, usage=usage)


class FaqGenGateway(Gateway):
    def __init__(self, megaservice, host="0.0.0.0", port=8888):
        super().__init__(
            megaservice, host, port, str(MegaServiceEndpoint.FAQ_GEN), ChatCompletionRequest, ChatCompletionResponse
        )

    async def handle_request(self, request: Request):
        data = await request.json()
        stream_opt = data.get("stream", True)
        chat_request = ChatCompletionRequest.parse_obj(data)
        prompt = self._handle_message(chat_request.messages)
        parameters = LLMParams(
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            streaming=stream_opt,
        )
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"query": prompt}, llm_parameters=parameters
        )
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
        return ChatCompletionResponse(model="faqgen", choices=choices, usage=usage)


class VisualQnAGateway(Gateway):
    def __init__(self, megaservice, host="0.0.0.0", port=8888):
        super().__init__(
            megaservice, host, port, str(MegaServiceEndpoint.VISUAL_QNA), ChatCompletionRequest, ChatCompletionResponse
        )

    async def handle_request(self, request: Request):
        data = await request.json()
        stream_opt = data.get("stream", False)
        chat_request = ChatCompletionRequest.parse_obj(data)
        prompt, images = self._handle_message(chat_request.messages)
        parameters = LLMParams(
            max_new_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            streaming=stream_opt,
        )
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"prompt": prompt, "image": images[0]}, llm_parameters=parameters
        )
        for node, response in result_dict.items():
            # Here it suppose the last microservice in the megaservice is LVM.
            if (
                isinstance(response, StreamingResponse)
                and node == list(self.megaservice.services.keys())[-1]
                and self.megaservice.services[node].service_type == ServiceType.LVM
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
        return ChatCompletionResponse(model="visualqna", choices=choices, usage=usage)


class VideoQnAGateway(Gateway):
    def __init__(self, megaservice, host="0.0.0.0", port=8888):
        super().__init__(
            megaservice,
            host,
            port,
            str(MegaServiceEndpoint.VIDEO_RAG_QNA),
            ChatCompletionRequest,
            ChatCompletionResponse,
        )

    async def handle_request(self, request: Request):
        data = await request.json()
        stream_opt = data.get("stream", False)
        chat_request = ChatCompletionRequest.parse_obj(data)
        prompt = self._handle_message(chat_request.messages)
        parameters = LLMParams(
            max_new_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            streaming=stream_opt,
        )
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"text": prompt}, llm_parameters=parameters
        )
        for node, response in result_dict.items():
            # Here it suppose the last microservice in the megaservice is LVM.
            if (
                isinstance(response, StreamingResponse)
                and node == list(self.megaservice.services.keys())[-1]
                and self.megaservice.services[node].service_type == ServiceType.LVM
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
        return ChatCompletionResponse(model="videoqna", choices=choices, usage=usage)


class RetrievalToolGateway(Gateway):
    """embed+retrieve+rerank."""

    def __init__(self, megaservice, host="0.0.0.0", port=8889):
        super().__init__(
            megaservice,
            host,
            port,
            str(MegaServiceEndpoint.RETRIEVALTOOL),
            Union[TextDoc, EmbeddingRequest, ChatCompletionRequest],  # ChatCompletionRequest,
            Union[RerankedDoc, LLMParamsDoc],  # ChatCompletionResponse
        )

    async def handle_request(self, request: Request):
        def parser_input(data, TypeClass, key):
            try:
                chat_request = TypeClass.parse_obj(data)
                query = getattr(chat_request, key)
            except:
                query = None
            return query

        data = await request.json()
        query = None
        for key, TypeClass in zip(["text", "input", "input"], [TextDoc, EmbeddingRequest, ChatCompletionRequest]):
            query = parser_input(data, TypeClass, key)
            if query is not None:
                break
        if query is None:
            raise ValueError(f"Unknown request type: {data}")
        result_dict, runtime_graph = await self.megaservice.schedule(initial_inputs={"text": query})
        last_node = runtime_graph.all_leaves()[-1]
        response = result_dict[last_node]
        print("response is ", response)
        return response


class MultimodalQnAGateway(Gateway):
    def __init__(self, multimodal_rag_megaservice, lvm_megaservice, host="0.0.0.0", port=9999):
        self.lvm_megaservice = lvm_megaservice
        super().__init__(
            multimodal_rag_megaservice,
            host,
            port,
            str(MegaServiceEndpoint.MULTIMODAL_QNA),
            ChatCompletionRequest,
            ChatCompletionResponse,
        )

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
            print("[ MultimodalQnAGateway ] stream=True not used, this has not support streaming yet!")
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

# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from fastapi import Request
from fastapi.responses import StreamingResponse

from ..proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
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


class ChatQnAGateway(Gateway):
    def __init__(self, megaservice, host="0.0.0.0", port=8888):
        super().__init__(
            megaservice, host, port, str(MegaServiceEndpoint.CHAT_QNA), ChatCompletionRequest, ChatCompletionResponse
        )

    async def handle_request(self, request: Request):
        data = await request.json()
        chat_request = ChatCompletionRequest.parse_obj(data)
        if isinstance(chat_request.messages, str):
            prompt = chat_request.messages
        else:
            for message in chat_request.messages:
                text_list = [item["text"] for item in message["content"] if item["type"] == "text"]
                prompt = "\n".join(text_list)
        await self.megaservice.schedule(initial_inputs={"text": prompt})
        for node, response in self.megaservice.result_dict.items():
            # Here it suppose the last microservice in the megaservice is LLM.
            if (
                isinstance(response, StreamingResponse)
                and node == list(self.megaservice.services.keys())[-1]
                and self.megaservice.services[node].service_type == ServiceType.LLM
            ):
                return response
        last_node = self.megaservice.all_leaves()[-1]
        response = self.megaservice.result_dict[last_node]["text"]
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
        chat_request = ChatCompletionRequest.parse_obj(data)
        if isinstance(chat_request.messages, str):
            prompt = chat_request.messages
        else:
            for message in chat_request.messages:
                text_list = [item["text"] for item in message["content"] if item["type"] == "text"]
                prompt = "\n".join(text_list)
        await self.megaservice.schedule(initial_inputs={"query": prompt})
        for node, response in self.megaservice.result_dict.items():
            # Here it suppose the last microservice in the megaservice is LLM.
            if (
                isinstance(response, StreamingResponse)
                and node == list(self.megaservice.services.keys())[-1]
                and self.megaservice.services[node].service_type == ServiceType.LLM
            ):
                return response
        last_node = self.megaservice.all_leaves()[-1]
        response = self.megaservice.result_dict[last_node]["text"]
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
        await self.megaservice.schedule(initial_inputs={"query": prompt})
        for node, response in self.megaservice.result_dict.items():
            # Here it suppose the last microservice in the megaservice is LLM.
            if (
                isinstance(response, StreamingResponse)
                and node == list(self.megaservice.services.keys())[-1]
                and self.megaservice.services[node].service_type == ServiceType.LLM
            ):
                return response
        last_node = self.megaservice.all_leaves()[-1]
        response = self.megaservice.result_dict[last_node]["text"]
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


class DocSumGateway(Gateway):
    def __init__(self, megaservice, host="0.0.0.0", port=8888):
        super().__init__(
            megaservice, host, port, str(MegaServiceEndpoint.DOC_SUMMARY), ChatCompletionRequest, ChatCompletionResponse
        )

    async def handle_request(self, request: Request):
        data = await request.json()
        chat_request = ChatCompletionRequest.parse_obj(data)
        if isinstance(chat_request.messages, str):
            prompt = chat_request.messages
        else:
            for message in chat_request.messages:
                text_list = [item["text"] for item in message["content"] if item["type"] == "text"]
                prompt = "\n".join(text_list)
        await self.megaservice.schedule(initial_inputs={"query": prompt})
        for node, response in self.megaservice.result_dict.items():
            # Here it suppose the last microservice in the megaservice is LLM.
            if (
                isinstance(response, StreamingResponse)
                and node == list(self.megaservice.services.keys())[-1]
                and self.megaservice.services[node].service_type == ServiceType.LLM
            ):
                return response
        last_node = self.megaservice.all_leaves()[-1]
        response = self.megaservice.result_dict[last_node]["text"]
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

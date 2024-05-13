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

import json
from typing import Dict, List

import requests
from fastapi import Request

from ..proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from .constants import MegaServiceEndpoint
from .dag import DAG
from .micro_service import MicroService


class ServiceOrchestrator(DAG):
    """Manage 1 or N micro services in a DAG through Python API."""

    def __init__(self, host="0.0.0.0", port=8000, endpoint=MegaServiceEndpoint.CHAT_QNA) -> None:
        self.services = {}  # all services, id -> service
        self.result_dict = {}
        self.host = host
        self.port = port
        self.endpoint = endpoint
        super().__init__()
        self.endpoints_info = {
            str(MegaServiceEndpoint.CHAT_QNA): (self.handle_chat_qna, ChatCompletionRequest, ChatCompletionResponse),
            str(MegaServiceEndpoint.CODE_GEN): (self.handle_code_gen, ChatCompletionRequest, ChatCompletionResponse),
            str(MegaServiceEndpoint.CODE_TRANS): (
                self.handle_code_trans,
                ChatCompletionRequest,
                ChatCompletionResponse,
            ),
        }
        self.endpoint_handler, self.input_datatype, self.output_datatype = self.endpoints_info[self.endpoint]
        self.gateway = MicroService(
            host=host,
            port=port,
            expose_endpoint=endpoint,
            input_datatype=self.input_datatype,
            output_datatype=self.output_datatype,
        )
        self.define_routes()

    def define_routes(self):
        self.gateway.app.router.add_api_route(self.endpoint, self.endpoint_func, methods=["POST"])
        self.gateway.app.router.add_api_route(str(MegaServiceEndpoint.LIST_SERVICE), self.list_service, methods=["GET"])
        self.gateway.app.router.add_api_route(
            str(MegaServiceEndpoint.LIST_PARAMETERS), self.list_parameter, methods=["GET"]
        )

    def start_server(self):
        self.gateway.start()

    def list_service(self):
        response = {}
        for node in self.all_leaves():
            response = {self.services[node].description: self.services[node].endpoint_path}
        return response

    def list_parameter(self):
        pass

    async def handle_chat_qna(self, request: Request):
        data = await request.json()
        chat_request = ChatCompletionRequest.parse_obj(data)
        if isinstance(chat_request.messages, str):
            prompt = chat_request.messages
        else:
            for message in chat_request.messages:
                text_list = [item["text"] for item in message["content"] if item["type"] == "text"]
                prompt = "\n".join(text_list)
        self.schedule(initial_inputs={"text": prompt})
        last_node = self.all_leaves()[-1]
        response = self.result_dict[last_node]["text"]
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

    async def handle_audio_qna(self, request: Request):
        data = await request.json()
        return {"message": "AudioQnA handler not implemented yet"}

    async def handle_visual_qna(self, request: Request):
        data = await request.json()
        return {"message": "VisualQnA handler not implemented yet"}

    async def handle_code_gen(self, request: Request):
        data = await request.json()
        chat_request = ChatCompletionRequest.parse_obj(data)
        if isinstance(chat_request.messages, str):
            prompt = chat_request.messages
        else:
            for message in chat_request.messages:
                text_list = [item["text"] for item in message["content"] if item["type"] == "text"]
                prompt = "\n".join(text_list)
        self.schedule(initial_inputs={"text": prompt})
        last_node = self.all_leaves()[-1]
        response = self.result_dict[last_node]["text"]
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

    async def handle_code_trans(self, request: Request):
        data = await request.json()
        chat_request = ChatCompletionRequest.parse_obj(data)
        if isinstance(chat_request.messages, str):
            prompt = chat_request.messages
        else:
            for message in chat_request.messages:
                text_list = [item["text"] for item in message["content"] if item["type"] == "text"]
                prompt = "\n".join(text_list)
        self.schedule(initial_inputs={"text": prompt})
        last_node = self.all_leaves()[-1]
        response = self.result_dict[last_node]["text"]
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

    async def handle_doc_summary(self, request: Request):
        data = await request.json()
        return {"message": "Document summary handler not implemented yet"}

    async def handle_search_qna(self, request: Request):
        data = await request.json()
        return {"message": "Search QnA handler not implemented yet"}

    async def handle_translation(self, request: Request):
        data = await request.json()
        return {"message": "Translation handler not implemented yet"}

    async def handle_embeddings(self, request: Request):
        data = await request.json()
        return {"message": "Embeddings handler not implemented yet"}

    async def handle_tts(self, request: Request):
        data = await request.json()
        return {"message": "Text-to-Speech handler not implemented yet"}

    async def handle_asr(self, request: Request):
        data = await request.json()
        return {"message": "Automatic Speech Recognition handler not implemented yet"}

    async def handle_chat(self, request: Request):
        data = await request.json()
        return {"message": "Chat handler not implemented yet"}

    async def handle_retrieval(self, request: Request):
        data = await request.json()
        return {"message": "Retrieval handler not implemented yet"}

    async def handle_reranking(self, request: Request):
        data = await request.json()
        return {"message": "Re-ranking handler not implemented yet"}

    async def handle_guardrails(self, request: Request):
        data = await request.json()
        return {"message": "Guardrails handler not implemented yet"}

    async def endpoint_func(self, request: Request):
        handler = self.endpoint_handler
        if handler is not None:
            return await handler(request)
        else:
            return {"error": "Invalid endpoint"}

    def add(self, service):
        if service.name not in self.services:
            self.services[service.name] = service
            self.add_node_if_not_exists(service.name)
        else:
            raise Exception(f"Service {service.name} already exists!")
        return self

    def flow_to(self, from_service, to_service):
        try:
            self.add_edge(from_service.name, to_service.name)
            return True
        except Exception as e:
            print(e)
            return False

    def schedule(self, initial_inputs: Dict):
        for node in self.topological_sort():
            if node in self.ind_nodes():
                inputs = initial_inputs
            else:
                inputs = self.process_outputs(self.predecessors(node))
            response = self.execute(node, inputs)
            self.dump_outputs(node, response)

    def process_outputs(self, prev_nodes: List) -> Dict:
        all_outputs = {}

        # assume all prev_nodes outputs' keys are not duplicated
        for prev_node in prev_nodes:
            all_outputs.update(self.result_dict[prev_node])
        return all_outputs

    def execute(self, cur_node: str, inputs: Dict):
        # send the cur_node request/reply
        endpoint = self.services[cur_node].endpoint_path
        response = requests.post(url=endpoint, data=json.dumps(inputs), proxies={"http": None})
        print(response)
        return response.json()

    def dump_outputs(self, node, response):
        self.result_dict[node] = response

    def get_all_final_outputs(self):
        for leaf in self.all_leaves():
            print(self.result_dict[leaf])

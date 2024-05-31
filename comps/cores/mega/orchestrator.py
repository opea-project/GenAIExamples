# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
from typing import Dict, List

import requests
from fastapi.responses import StreamingResponse

from ..proto.docarray import LLMParams
from .constants import ServiceType
from .dag import DAG


class ServiceOrchestrator(DAG):
    """Manage 1 or N micro services in a DAG through Python API."""

    def __init__(self) -> None:
        self.services = {}  # all services, id -> service
        self.result_dict = {}
        super().__init__()

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

    async def schedule(self, initial_inputs: Dict, llm_parameters: LLMParams = LLMParams()):
        for node in self.topological_sort():
            if node in self.ind_nodes():
                inputs = initial_inputs
            else:
                inputs = self.process_outputs(self.predecessors(node))
            response = await self.execute(node, inputs, llm_parameters)
            self.dump_outputs(node, response)

    def process_outputs(self, prev_nodes: List) -> Dict:
        all_outputs = {}

        # assume all prev_nodes outputs' keys are not duplicated
        for prev_node in prev_nodes:
            all_outputs.update(self.result_dict[prev_node])
        return all_outputs

    async def execute(self, cur_node: str, inputs: Dict, llm_parameters: LLMParams = LLMParams()):
        # send the cur_node request/reply
        endpoint = self.services[cur_node].endpoint_path
        llm_parameters_dict = llm_parameters.dict()
        for field, value in llm_parameters_dict.items():
            if inputs.get(field) != value:
                inputs[field] = value
        if self.services[cur_node].service_type == ServiceType.LLM and llm_parameters.streaming:
            response = requests.post(
                url=endpoint, data=json.dumps(inputs), proxies={"http": None}, stream=True, timeout=1000
            )

            def generate():
                if response:
                    for chunk in response.iter_content(chunk_size=None):
                        if chunk:
                            yield chunk

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            response = requests.post(url=endpoint, data=json.dumps(inputs), proxies={"http": None})
            print(response)
            return response.json()

    def dump_outputs(self, node, response):
        self.result_dict[node] = response

    def get_all_final_outputs(self):
        for leaf in self.all_leaves():
            print(self.result_dict[leaf])

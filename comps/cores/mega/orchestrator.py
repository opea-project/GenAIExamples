# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import copy
import json
import re
from typing import Dict, List

import aiohttp
import requests
from fastapi.responses import StreamingResponse

from ..proto.docarray import LLMParams
from .constants import ServiceType
from .dag import DAG


class ServiceOrchestrator(DAG):
    """Manage 1 or N micro services in a DAG through Python API."""

    def __init__(self) -> None:
        self.services = {}  # all services, id -> service
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
        result_dict = {}
        runtime_graph = DAG()
        runtime_graph.graph = copy.deepcopy(self.graph)

        timeout = aiohttp.ClientTimeout(total=1000)
        async with aiohttp.ClientSession(trust_env=True, timeout=timeout) as session:
            pending = {
                asyncio.create_task(self.execute(session, node, initial_inputs, runtime_graph))
                for node in self.ind_nodes()
            }
            ind_nodes = self.ind_nodes()

            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                for done_task in done:
                    response, node = await done_task
                    self.dump_outputs(node, response, result_dict)

                    # traverse the current node's downstream nodes and execute if all one's predecessors are finished
                    downstreams = runtime_graph.downstream(node)

                    # remove all the black nodes that are skipped to be forwarded to
                    if not isinstance(response, StreamingResponse) and "downstream_black_list" in response:
                        for black_node in response["downstream_black_list"]:
                            for downstream in reversed(downstreams):
                                try:
                                    if re.findall(black_node, downstream):
                                        print(f"skip forwardding to {downstream}...")
                                        runtime_graph.delete_edge(node, downstream)
                                        downstreams.remove(downstream)
                                except re.error as e:
                                    print("Pattern invalid! Operation cancelled.")

                    for d_node in downstreams:
                        if all(i in result_dict for i in runtime_graph.predecessors(d_node)):
                            inputs = self.process_outputs(runtime_graph.predecessors(d_node), result_dict)
                            pending.add(
                                asyncio.create_task(
                                    self.execute(session, d_node, inputs, runtime_graph, llm_parameters)
                                )
                            )
        nodes_to_keep = []
        for i in ind_nodes:
            nodes_to_keep.append(i)
            nodes_to_keep.extend(runtime_graph.all_downstreams(i))

        all_nodes = list(runtime_graph.graph.keys())

        for node in all_nodes:
            if node not in nodes_to_keep:
                runtime_graph.delete_node_if_exists(node)

        return result_dict, runtime_graph

    def process_outputs(self, prev_nodes: List, result_dict: Dict) -> Dict:
        all_outputs = {}

        # assume all prev_nodes outputs' keys are not duplicated
        for prev_node in prev_nodes:
            all_outputs.update(result_dict[prev_node])
        return all_outputs

    async def execute(
        self,
        session: aiohttp.client.ClientSession,
        cur_node: str,
        inputs: Dict,
        runtime_graph: DAG,
        llm_parameters: LLMParams = LLMParams(),
    ):
        # send the cur_node request/reply
        endpoint = self.services[cur_node].endpoint_path
        llm_parameters_dict = llm_parameters.dict()
        for field, value in llm_parameters_dict.items():
            if inputs.get(field) != value:
                inputs[field] = value

        if self.services[cur_node].service_type == ServiceType.LLM and llm_parameters.streaming:
            # Still leave to sync requests.post for StreamingResponse
            response = requests.post(
                url=endpoint, data=json.dumps(inputs), proxies={"http": None}, stream=True, timeout=1000
            )

            def generate():
                if response:
                    for chunk in response.iter_content(chunk_size=None):
                        if chunk:
                            yield chunk

            return StreamingResponse(generate(), media_type="text/event-stream"), cur_node
        else:
            if (
                self.services[cur_node].service_type == ServiceType.LLM
                and runtime_graph.predecessors(cur_node)
                and "asr" in runtime_graph.predecessors(cur_node)[0]
            ):
                inputs["query"] = inputs["text"]
                del inputs["text"]
            async with session.post(endpoint, json=inputs) as response:
                print(response.status)
                return await response.json(), cur_node

    def dump_outputs(self, node, response, result_dict):
        result_dict[node] = response

    def get_all_final_outputs(self, result_dict, runtime_graph):
        final_output_dict = {}
        for leaf in runtime_graph.all_leaves():
            final_output_dict[leaf] = result_dict[leaf]
        return final_output_dict

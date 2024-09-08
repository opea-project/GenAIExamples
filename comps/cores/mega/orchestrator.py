# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import copy
import json
import os
import re
from typing import Dict, List

import aiohttp
import requests
from fastapi.responses import StreamingResponse

from ..proto.docarray import LLMParams
from .constants import ServiceType
from .dag import DAG
from .logger import CustomLogger

logger = CustomLogger("comps-core-orchestrator")
LOGFLAG = os.getenv("LOGFLAG", False)


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
            logger.error(e)
            return False

    async def schedule(self, initial_inputs: Dict, llm_parameters: LLMParams = LLMParams(), **kwargs):
        result_dict = {}
        runtime_graph = DAG()
        runtime_graph.graph = copy.deepcopy(self.graph)
        if LOGFLAG:
            logger.info(initial_inputs)

        timeout = aiohttp.ClientTimeout(total=1000)
        async with aiohttp.ClientSession(trust_env=True, timeout=timeout) as session:
            pending = {
                asyncio.create_task(
                    self.execute(session, node, initial_inputs, runtime_graph, llm_parameters, **kwargs)
                )
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
                                        if LOGFLAG:
                                            logger.info(f"skip forwardding to {downstream}...")
                                        runtime_graph.delete_edge(node, downstream)
                                        downstreams.remove(downstream)
                                except re.error as e:
                                    logger.error("Pattern invalid! Operation cancelled.")
                            if len(downstreams) == 0 and llm_parameters.streaming:
                                # turn the response to a StreamingResponse
                                # to make the response uniform to UI
                                def fake_stream(text):
                                    yield "data: b'" + text + "'\n\n"
                                    yield "data: [DONE]\n\n"

                                self.dump_outputs(
                                    node,
                                    StreamingResponse(fake_stream(response["text"]), media_type="text/event-stream"),
                                    result_dict,
                                )

                    for d_node in downstreams:
                        if all(i in result_dict for i in runtime_graph.predecessors(d_node)):
                            inputs = self.process_outputs(runtime_graph.predecessors(d_node), result_dict)
                            pending.add(
                                asyncio.create_task(
                                    self.execute(session, d_node, inputs, runtime_graph, llm_parameters, **kwargs)
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
        **kwargs,
    ):
        # send the cur_node request/reply
        endpoint = self.services[cur_node].endpoint_path
        llm_parameters_dict = llm_parameters.dict()
        if (
            self.services[cur_node].service_type == ServiceType.LLM
            or self.services[cur_node].service_type == ServiceType.LVM
        ):
            for field, value in llm_parameters_dict.items():
                if inputs.get(field) != value:
                    inputs[field] = value

        # pre-process
        inputs = self.align_inputs(inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs)

        if (
            self.services[cur_node].service_type == ServiceType.LLM
            or self.services[cur_node].service_type == ServiceType.LVM
        ) and llm_parameters.streaming:
            # Still leave to sync requests.post for StreamingResponse
            if LOGFLAG:
                logger.info(inputs)
            response = requests.post(
                url=endpoint,
                data=json.dumps(inputs),
                headers={"Content-type": "application/json"},
                proxies={"http": None},
                stream=True,
                timeout=1000,
            )
            downstream = runtime_graph.downstream(cur_node)
            if downstream:
                assert len(downstream) == 1, "Not supported multiple streaming downstreams yet!"
                cur_node = downstream[0]
                hitted_ends = [".", "?", "!", "。", "，", "！"]
                downstream_endpoint = self.services[downstream[0]].endpoint_path

            def generate():
                if response:
                    buffered_chunk_str = ""
                    for chunk in response.iter_content(chunk_size=None):
                        if chunk:
                            if downstream:
                                chunk = chunk.decode("utf-8")
                                buffered_chunk_str += self.extract_chunk_str(chunk)
                                is_last = chunk.endswith("[DONE]\n\n")
                                if (buffered_chunk_str and buffered_chunk_str[-1] in hitted_ends) or is_last:
                                    res = requests.post(
                                        url=downstream_endpoint,
                                        data=json.dumps({"text": buffered_chunk_str}),
                                        proxies={"http": None},
                                    )
                                    res_json = res.json()
                                    if "text" in res_json:
                                        res_txt = res_json["text"]
                                    else:
                                        raise Exception("Other response types not supported yet!")
                                    buffered_chunk_str = ""  # clear
                                    yield from self.token_generator(res_txt, is_last=is_last)
                            else:
                                yield chunk

            return (
                StreamingResponse(self.align_generator(generate(), **kwargs), media_type="text/event-stream"),
                cur_node,
            )
        else:
            if LOGFLAG:
                logger.info(inputs)
            async with session.post(endpoint, json=inputs) as response:
                # Parse as JSON
                data = await response.json()
                # post process
                data = self.align_outputs(data, cur_node, inputs, runtime_graph, llm_parameters_dict, **kwargs)

                return data, cur_node

    def align_inputs(self, inputs, *args, **kwargs):
        """Override this method in megaservice definition."""
        return inputs

    def align_outputs(self, data, *args, **kwargs):
        """Override this method in megaservice definition."""
        return data

    def align_generator(self, gen, *args, **kwargs):
        """Override this method in megaservice definition."""
        return gen

    def dump_outputs(self, node, response, result_dict):
        result_dict[node] = response

    def get_all_final_outputs(self, result_dict, runtime_graph):
        final_output_dict = {}
        for leaf in runtime_graph.all_leaves():
            final_output_dict[leaf] = result_dict[leaf]
        return final_output_dict

    def extract_chunk_str(self, chunk_str):
        if chunk_str == "data: [DONE]\n\n":
            return ""
        prefix = "data: b'"
        prefix_2 = 'data: b"'
        suffix = "'\n\n"
        suffix_2 = '"\n\n'
        if chunk_str.startswith(prefix) or chunk_str.startswith(prefix_2):
            chunk_str = chunk_str[len(prefix) :]
        if chunk_str.endswith(suffix) or chunk_str.endswith(suffix_2):
            chunk_str = chunk_str[: -len(suffix)]
        return chunk_str

    def token_generator(self, sentence, is_last=False):
        prefix = "data: "
        suffix = "\n\n"
        tokens = re.findall(r"\s?\S+\s?", sentence, re.UNICODE)
        for token in tokens:
            yield prefix + repr(token.replace("\\n", "\n").encode("utf-8")) + suffix
        if is_last:
            yield "data: [DONE]\n\n"

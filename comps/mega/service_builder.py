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
import os
import re
import subprocess
import time
from collections import OrderedDict, defaultdict
from typing import Dict, List, Optional, Tuple

import requests
import yaml
from dag import DAG


class BaseService:
    def __init__(self, id, endpoint) -> None:
        """The base service object contains an id and an endpoint url."""
        self.id = id
        self.endpoint = endpoint


class ServiceBuilder(DAG):
    """Manage 1 or N micro services in a DAG through Python API."""

    def __init__(self, host="localhost", port=8000, hostfile=None) -> None:
        self.services = {}  # all services, id -> service
        self.result_dict = {}
        super().__init__()

    def add(self, service):
        if service.id not in self.services:
            self.services[service.id] = service
            self.add_node_if_not_exists(service.id)
        else:
            raise Exception(f"Service {service.id} already exists!")
        return self

    def flow_to(self, from_service, to_service):
        try:
            self.add_edge(from_service.id, to_service.id)
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
        endpoint = self.services[cur_node].endpoint
        response = requests.post(url=endpoint, data=json.dumps({"number": inputs["number"]}), proxies={"http": None})
        print(response)
        return response.json()

    def dump_outputs(self, node, response):
        self.result_dict[node] = response

    def get_all_final_outputs(self):

        for leaf in self.all_leaves():
            print(self.result_dict[leaf])

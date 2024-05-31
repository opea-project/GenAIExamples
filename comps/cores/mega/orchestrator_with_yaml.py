# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import re
from collections import OrderedDict
from typing import Dict, List, Tuple

import requests
import yaml

from .dag import DAG


class ServiceOrchestratorWithYaml(DAG):
    """Manage 1 or N micro services in a DAG defined by YAML."""

    def __init__(self, yaml_file_path: str):
        self.yaml_file_path = yaml_file_path
        self.result_dict = {}  # {node: node's dict output}
        super().__init__()
        self.docs, is_valid = self._load_from_yaml()
        if not is_valid:
            raise Exception("Invalid mega graph!")

    def execute(self, cur_node: str, inputs: Dict):
        # send the cur_node request/reply
        endpoint = self.docs["opea_micro_services"][cur_node]["endpoint"]
        response = requests.post(url=endpoint, data=json.dumps(inputs), proxies={"http": None})
        print(response)
        return response.json()

    def dump_outputs(self, node, response):
        self.result_dict[node] = response

    def get_all_final_outputs(self):

        for leaf in self.all_leaves():
            print(self.result_dict[leaf])

    def process_outputs(self, prev_nodes: List) -> Dict:
        all_outputs = {}
        # assume all prev_nodes outputs' keys are not duplicated
        for prev_node in prev_nodes:
            all_outputs.update(self.result_dict[prev_node])
        return all_outputs

    async def schedule(self, initial_inputs: Dict):
        for node in self.topological_sort():
            if node in self.ind_nodes():
                inputs = initial_inputs
            else:
                inputs = self.process_outputs(self.predecessors(node))
            response = self.execute(node, inputs)
            self.dump_outputs(node, response)

    def _load_from_yaml(self):
        """Parse the yaml and output docs, whether the mega graph is valid, the mega graph."""
        with open(self.yaml_file_path) as file:
            docs = yaml.safe_load(file)

        if "mega_flow" in docs["opea_mega_service"]:
            mega_flow = docs["opea_mega_service"]["mega_flow"]
            return docs, self._construct_dag_from_rules(mega_flow)
        else:
            node_ids = docs["opea_micro_services"]
            return docs, self._construct_dag_from_nodes(node_ids)

    def _construct_dag_from_nodes(self, nodes: List[str]) -> Tuple[bool, OrderedDict]:
        for cur_node in nodes:
            self.add_node_if_not_exists(cur_node)
        return True

    def _construct_dag_from_rules(self, rules: List[str]) -> Tuple[bool, OrderedDict]:
        """rules: ['(s1, s2) >> s3', 's3 >> (s4, s5)']
        ['(s1, s2) >> s3 >> (s4, s5)']
        """
        is_valid = True
        for rule in rules:
            node_groups = [i.strip() for i in rule.split(">>")]  # ['(s1, s2)', 's3']
            prev_nodes = None
            for node_group_str in node_groups:

                if node_group_str.startswith("(") and node_group_str.endswith(")"):
                    cur_nodes = [i.strip() for i in re.findall(r"\((.*)\)", node_group_str)[0].split(",")]
                    for cur_node in cur_nodes:
                        self.add_node_if_not_exists(cur_node)
                else:
                    cur_nodes = [node_group_str]
                    self.add_node_if_not_exists(node_group_str)
                if prev_nodes:
                    try:
                        for prev_node in prev_nodes:
                            for cur_node in cur_nodes:
                                self.add_edge(prev_node, cur_node)
                    except Exception as e:
                        print("**********")
                        print(f"add edge fail! {prev_node} >> {cur_node}")
                        print(e)
                        print("**********")
                        is_valid = False
                        self.reset_graph()
                        break
                prev_nodes = cur_nodes
        return is_valid

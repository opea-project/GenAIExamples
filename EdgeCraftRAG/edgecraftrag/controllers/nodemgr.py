# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import List

from edgecraftrag.api_schema import IndexerIn, ModelIn, NodeParserIn
from edgecraftrag.base import BaseComponent, BaseMgr, CallbackType, ModelType
from llama_index.core.schema import BaseNode


class NodeMgr:

    def __init__(self):
        self.nodes = {}

    # idx: index of node_parser
    def add_nodes(self, np_idx, nodes):
        if np_idx in self.nodes:
            self.nodes[np_idx].append(nodes)
        else:
            self.nodes[np_idx] = nodes

    # TODO: to be implemented
    def del_nodes(self, nodes):
        pass

    def del_nodes_by_np_idx(self, np_idx):
        if np_idx in self.nodes:
            del self.nodes[np_idx]

    def get_nodes(self, np_idx) -> List[BaseNode]:
        if np_idx in self.nodes:
            return self.nodes[np_idx]
        else:
            return []

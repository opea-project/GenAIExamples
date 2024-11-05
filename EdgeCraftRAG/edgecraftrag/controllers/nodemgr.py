from edgecraftrag.base import (
    BaseComponent,
    BaseMgr,
    CallbackType,
    ModelType
)

from edgecraftrag.api_schema import NodeParserIn, IndexerIn, ModelIn
from typing import List
from llama_index.core.schema import (
    BaseNode,
)


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
        del self.nodes[np_idx]

    def get_nodes(self, np_idx) -> List[BaseNode]:
        if np_idx in self.nodes:
            return self.nodes[np_idx]
        else:
            return []

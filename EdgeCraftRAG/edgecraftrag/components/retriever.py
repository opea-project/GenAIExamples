# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any, List, cast

from edgecraftrag.base import BaseComponent, CompType, RetrieverType
from llama_index.core.indices.vector_store.retrievers import VectorIndexRetriever
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.schema import BaseNode
from llama_index.retrievers.bm25 import BM25Retriever
from pydantic import model_serializer


class VectorSimRetriever(BaseComponent, VectorIndexRetriever):

    def __init__(self, indexer, **kwargs):
        BaseComponent.__init__(
            self,
            comp_type=CompType.RETRIEVER,
            comp_subtype=RetrieverType.VECTORSIMILARITY,
        )
        VectorIndexRetriever.__init__(
            self,
            index=indexer,
            node_ids=list(indexer.index_struct.nodes_dict.values()),
            callback_manager=indexer._callback_manager,
            object_map=indexer._object_map,
            **kwargs,
        )
        # This might be a bug of llamaindex retriever.
        # The node_ids will never be updated after the retriever's
        # creation. However, the node_ids decides the available node
        # ids to be retrieved which means the target nodes to be
        # retrieved are freezed to the time of the retriever's creation.
        self._node_ids = None

    def run(self, **kwargs) -> Any:
        for k, v in kwargs.items():
            if k == "query":
                return self.retrieve(v)

        return None

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "retriever_type": self.comp_subtype,
            "retrieve_topk": self.similarity_top_k,
        }
        return set


class AutoMergeRetriever(BaseComponent, AutoMergingRetriever):

    def __init__(self, indexer, **kwargs):
        BaseComponent.__init__(
            self,
            comp_type=CompType.RETRIEVER,
            comp_subtype=RetrieverType.AUTOMERGE,
        )
        self._index = indexer
        self.topk = kwargs["similarity_top_k"]

        AutoMergingRetriever.__init__(
            self,
            vector_retriever=indexer.as_retriever(**kwargs),
            storage_context=indexer._storage_context,
            object_map=indexer._object_map,
            callback_manager=indexer._callback_manager,
        )

    def run(self, **kwargs) -> Any:
        for k, v in kwargs.items():
            if k == "query":
                # vector_retriever needs to be updated
                self._vector_retriever = self._index.as_retriever(similarity_top_k=self.topk)
                return self.retrieve(v)

        return None


class SimpleBM25Retriever(BaseComponent):
    # The nodes parameter in BM25Retriever is not from index,
    # nodes in BM25Retriever can not be updated through 'indexer.insert_nodes()',
    # which means nodes should be passed to BM25Retriever after data preparation stage, not init stage

    def __init__(self, indexer, **kwargs):
        BaseComponent.__init__(
            self,
            comp_type=CompType.RETRIEVER,
            comp_subtype=RetrieverType.BM25,
        )
        self._docstore = indexer._docstore
        self.topk = kwargs["similarity_top_k"]

    def run(self, **kwargs) -> Any:
        for k, v in kwargs.items():
            if k == "query":
                nodes = cast(List[BaseNode], list(self._docstore.docs.values()))
                similarity_top_k = min(len(nodes), self.topk)
                bm25_retr = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=similarity_top_k)
                return bm25_retr.retrieve(v)

        return None

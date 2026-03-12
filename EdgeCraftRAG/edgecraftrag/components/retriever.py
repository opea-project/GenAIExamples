# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import warnings
from typing import Any, List, Optional, cast

import requests
from edgecraftrag.base import BaseComponent, CompType, RetrieverType
from llama_index.core.indices.vector_store.retrievers import VectorIndexRetriever
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.schema import BaseNode, Document, NodeWithScore
from llama_index.retrievers.bm25 import BM25Retriever
from pydantic import model_serializer


class VectorSimRetriever(BaseComponent, VectorIndexRetriever):

    def __init__(self, indexer, **kwargs):
        BaseComponent.__init__(
            self,
            comp_type=CompType.RETRIEVER,
            comp_subtype=RetrieverType.VECTORSIMILARITY,
        )
        self.topk = kwargs["similarity_top_k"]

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
                top_k = kwargs["top_k"] if kwargs["top_k"] else self.topk
                self.similarity_top_k = top_k
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
                top_k = kwargs["top_k"] if kwargs["top_k"] else self.topk
                # vector_retriever needs to be updated
                self._vector_retriever = self._index.as_retriever(similarity_top_k=top_k)
                return self.retrieve(v)

        return None

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "retriever_type": self.comp_subtype,
            "retrieve_topk": self.topk,
        }
        return set


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
        self._index = indexer

    def run(self, **kwargs) -> Any:
        for k, v in kwargs.items():
            if k == "query":
                if self._index.comp_subtype == "milvus_vector":
                    raise NotImplementedError("not support BM25 retriever for Milvus vector store")
                top_k = kwargs["top_k"] if kwargs["top_k"] else self.topk
                nodes = cast(List[BaseNode], list(self._docstore.docs.values()))
                similarity_top_k = min(len(nodes), top_k)
                bm25_retr = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=similarity_top_k)
                return bm25_retr.retrieve(v)

        return None

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "retriever_type": self.comp_subtype,
            "retrieve_topk": self.topk,
        }
        return set


class KBadminRetriever(BaseComponent):
    def __init__(self, indexer, **kwargs):
        BaseComponent.__init__(
            self,
            comp_type=CompType.RETRIEVER,
            comp_subtype=RetrieverType.KBADMIN_RETRIEVER,
        )
        self.vector_db = indexer.vector_db
        self.collection_name = None
        self.topk = kwargs.get("similarity_top_k", 30)
        self.embedding_model_name = indexer.embed_model
        self.embedding_url = indexer.kbadmin_embedding_url
        self.embedding = indexer.embedding
        self._index = indexer

    def similarity_search_with_embedding(self, query: str, k) -> list[tuple[Document, float]]:
        url = self.embedding_url + "/embeddings"
        embedding_info = {"model": self.embedding_model_name, "input": query}
        # Get embedding result from embedding service
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=embedding_info)
        embedding_json = response.json()
        embedding = embedding_json["data"][0]["embedding"]
        docs_and_scores = self.vector_db.similarity_search_with_score_by_vector(embedding=embedding, k=k)
        relevance_score_fn = self.vector_db._select_relevance_score_fn()
        return [(doc, relevance_score_fn(score)) for doc, score in docs_and_scores]

    def run(self, **kwargs) -> Any:
        query = kwargs["query"]
        top_k = kwargs["top_k"] if kwargs["top_k"] else self.topk
        # langchain retrieval
        docs_and_similarities = self.similarity_search_with_embedding(query=query, k=top_k)
        node_with_scores: List[NodeWithScore] = []
        for doc, similarity in docs_and_similarities:
            score: Optional[float] = None
            if similarity is not None:
                score = similarity
            # convert langchain store format into llamaindex
            node = Document.from_langchain_format(doc)
            node_with_scores.append(NodeWithScore(node=node, score=score))
        return node_with_scores

    @model_serializer
    def ser_model(self):
        set = {"idx": self.idx, "retriever_type": self.comp_subtype}
        return set

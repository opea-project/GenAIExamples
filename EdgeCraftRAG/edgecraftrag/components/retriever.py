# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import warnings
from typing import Any, List, Optional, cast

import requests
from edgecraftrag.base import BaseComponent, CompType, RetrieverType
from langchain_milvus import Milvus
from langchain_openai import OpenAIEmbeddings
from llama_index.core.indices.vector_store.retrievers import VectorIndexRetriever
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.schema import BaseNode, Document, NodeWithScore
from llama_index.retrievers.bm25 import BM25Retriever
from pydantic import model_serializer
from pymilvus import Collection, MilvusException, connections, utility


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

    def run(self, **kwargs) -> Any:
        for k, v in kwargs.items():
            if k == "query":
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
        self.vector_db = None
        self.collection_name = None
        self.topk = kwargs.get("similarity_top_k", 30)
        self.KBADMIN_MILVUS_URL = indexer.vector_url
        self.CONNECTION_ARGS = {"uri": indexer.vector_url}
        self.vector_field = "q_1024_vec"
        self.text_field = "content_with_weight"
        self.embedding_model_name = indexer.embed_model
        self.embedding_url = indexer.kbadmin_embedding_url + "/v3"
        self.embedding = OpenAIEmbeddings(
            model=self.embedding_model_name,
            api_key="unused",
            base_url=self.embedding_url,
            tiktoken_enabled=False,
            embedding_ctx_length=510,
        )

    def config_kbadmin_milvus(self, knowledge_name):
        collection_name = knowledge_name
        if not kbs_rev_maps:
            get_kbs_info(self.CONNECTION_ARGS)
        collection_name = kbs_rev_maps[collection_name]
        self.vector_db = Milvus(
            self.embedding,
            connection_args=self.CONNECTION_ARGS,
            collection_name=collection_name,
            vector_field=self.vector_field,
            text_field=self.text_field,
            enable_dynamic_field=True,
            index_params={"index_type": "FLAT", "metric_type": "IP", "params": {}},
        )

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
        set = {"idx": self.idx, "retriever_type": self.comp_subtype, "CONNECTION_ARGS": self.CONNECTION_ARGS}
        return set


# global kbs maps.
global kbs_rev_maps
kbs_rev_maps = {}


def get_kbs_info(CONNECTION_ARGS):
    alias = "default"
    try:
        connections.connect("default", **CONNECTION_ARGS)
        collections = utility.list_collections()
        all_kb_infos = {}
        new_infos = {}
        for kb in collections:
            collection = Collection(kb)
            collection.load()
            try:
                if any(field.name == "kb_id" for field in collection.schema.fields):
                    docs = collection.query(
                        expr="pk != 0",
                        output_fields=["kb_name", "kb_id", "docnm_kwd"],
                        timeout=10,
                    )
                else:
                    docs = collection.query(
                        expr="pk != 0",
                        output_fields=["filename"],
                        timeout=10,
                    )
                collection.release()
            except MilvusException as e:
                continue
            this_kbinfo = {}
            for doc in docs:
                try:
                    if "kb_name" in doc:
                        if not this_kbinfo:
                            this_kbinfo["name"] = doc["kb_name"]
                            this_kbinfo["uuid"] = doc["kb_id"]
                            this_kbinfo["files"] = set([doc["docnm_kwd"]])
                        else:
                            this_kbinfo["files"].add(doc["docnm_kwd"])
                    else:
                        if not this_kbinfo:
                            this_kbinfo["name"] = kb
                            this_kbinfo["uuid"] = ""
                            this_kbinfo["files"] = set([doc["filename"]])
                        else:
                            this_kbinfo["files"].add(doc["filename"])
                except KeyError:
                    this_kbinfo = None
                    break
            if this_kbinfo:
                unique_files = list(this_kbinfo["files"])
                this_kbinfo["files"] = unique_files
                new_infos[kb] = this_kbinfo
        all_kb_infos.update(new_infos)
        kbs_rev_maps.clear()
        for kb_id in all_kb_infos:
            kbs_rev_maps[all_kb_infos[kb_id]["name"]] = kb_id
        return kbs_rev_maps
    finally:
        if connections.has_connection(alias):
            connections.disconnect(alias)

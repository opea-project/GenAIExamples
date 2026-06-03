# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any

import faiss
from edgecraftrag.base import BaseComponent, CompType, IndexerType
from edgecraftrag.context import ctx
from langchain_openai import OpenAIEmbeddings
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.vector_stores.milvus import MilvusVectorStore
from pydantic import model_serializer
from langchain_milvus import Milvus
from pymilvus import Collection, MilvusException, connections, utility

class VectorIndexer(BaseComponent, VectorStoreIndex):
    def __init__(self, embed_model, vector_type, vector_url="http://localhost:19530", kb_name="default_kb"):
        BaseComponent.__init__(
            self,
            comp_type=CompType.INDEXER,
            comp_subtype=vector_type,
        )
        self.model = embed_model
        if not embed_model:
            # Settings.embed_model should be set to None when embed_model is None to avoid 'no oneapi key' error
            from llama_index.core import Settings

            Settings.embed_model = None
        self.vector_url = vector_url
        self._initialize_indexer(embed_model, vector_type, vector_url, kb_name)

    def _initialize_indexer(self, embed_model, vector_type, vector_url, kb_name):
        collection_name = kb_name
        if embed_model:
            try:
                self.d = len(embed_model.get_text_embedding("test"))
            except Exception:
                # Fallback for OpenVINO models if the above fails
                self.d = embed_model._model.request.outputs[0].get_partial_shape()[2].get_length()
        else:
            self.d = 128
        match vector_type:
            case IndexerType.DEFAULT_VECTOR:
                VectorStoreIndex.__init__(self, embed_model=embed_model, nodes=[])
            case IndexerType.FAISS_VECTOR:
                faiss_index = faiss.IndexFlatL2(self.d)
                faiss_store = StorageContext.from_defaults(vector_store=FaissVectorStore(faiss_index=faiss_index))
                VectorStoreIndex.__init__(self, embed_model=embed_model, nodes=[], storage_context=faiss_store)
            case IndexerType.MILVUS_VECTOR:
                milvus_vector_store = MilvusVectorStore(
                    uri=vector_url,
                    dim=self.d,
                    collection_name=collection_name,
                    overwrite=False,
                )
                milvus_store = StorageContext.from_defaults(vector_store=milvus_vector_store)
                VectorStoreIndex.__init__(self, embed_model=embed_model, nodes=[], storage_context=milvus_store)

    def reinitialize_indexer(self, kb_name="default_kb"):
        self._initialize_indexer(self.model, self.comp_subtype, self.vector_url, kb_name)

    def clear_milvus_collection(self, kb_name="default_kb"):
        milvus_vector_store = MilvusVectorStore(
            uri=self.vector_url,
            dim=self.d,
            collection_name=kb_name,
            overwrite=False,
        )
        milvus_vector_store.clear()

    def run(self, **kwargs) -> Any:
        pass

    @model_serializer
    def ser_model(self):
        set = {"idx": self.idx, "indexer_type": self.comp_subtype, "model": self.model}
        return set


class KBADMINIndexer(BaseComponent):
    # Handled in the kbadmin project
    def __init__(self, embed_model, vector_type, kbadmin_embedding_url, vector_url="http://localhost:29530"):
        BaseComponent.__init__(
            self,
            comp_type=CompType.INDEXER,
            comp_subtype=IndexerType.KBADMIN_INDEXER,
        )
        self.embed_model = embed_model
        self.kbadmin_embedding_url = kbadmin_embedding_url + "/v3"
        self.vector_url = vector_url
        self.CONNECTION_ARGS = {"uri": self.vector_url}
        self.vector_field = "q_1024_vec"
        self.text_field = "content_with_weight"
        self.embedding = OpenAIEmbeddings(
            model=embed_model,
            api_key="unused",
            base_url=self.kbadmin_embedding_url,
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

    def insert_nodes(self, nodes):
        return None

    def _index_struct(self, nodes):
        return None

    def run(self, **kwargs) -> Any:
        return None

    def reinitialize_indexer(self, kb_name="default_kb"):
        return None

    def clear_milvus_collection(self, **kwargs):
        return None

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "indexer_type": self.comp_subtype,
            "model": {"model_id": self.embed_model},
            "kbadmin_embedding_url": self.kbadmin_embedding_url,
            "vector_url": self.vector_url,
        }
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

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any

import faiss
from edgecraftrag.base import BaseComponent, CompType, IndexerType
from edgecraftrag.context import ctx
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.vector_stores.milvus import MilvusVectorStore
from pydantic import model_serializer


class VectorIndexer(BaseComponent, VectorStoreIndex):

    def __init__(self, embed_model, vector_type, milvus_uri="http://localhost:19530", kb_name="default_kb"):
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
        self.milvus_uri = milvus_uri
        self._initialize_indexer(embed_model, vector_type, milvus_uri, kb_name)

    def _initialize_indexer(self, embed_model, vector_type, milvus_uri, kb_name):
        # get active name
        pl = ctx.get_pipeline_mgr().get_active_pipeline()
        plname = pl.name if pl else ""
        if embed_model:
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
                    uri=milvus_uri,
                    dim=self.d,
                    collection_name=kb_name + plname + str(self.d),
                    overwrite=False,
                )
                milvus_store = StorageContext.from_defaults(vector_store=milvus_vector_store)
                VectorStoreIndex.__init__(self, embed_model=embed_model, nodes=[], storage_context=milvus_store)

    def reinitialize_indexer(self, kb_name="default_kb"):
        self._initialize_indexer(self.model, self.comp_subtype, self.milvus_uri, kb_name)

    def clear_milvus_collection(self, kb_name="default_kb"):
        # get active name
        pl = ctx.get_pipeline_mgr().get_active_pipeline()
        plname = pl.name if pl else ""
        milvus_vector_store = MilvusVectorStore(
            uri=self.milvus_uri,
            collection_name=kb_name + plname + str(self.d),
            overwrite=False,
        )
        milvus_vector_store.clear()

    def run(self, **kwargs) -> Any:
        pass

    @model_serializer
    def ser_model(self):
        set = {"idx": self.idx, "indexer_type": self.comp_subtype, "model": self.model}
        return set

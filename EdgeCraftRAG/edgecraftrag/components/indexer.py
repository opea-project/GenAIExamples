# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any

import faiss
from edgecraftrag.base import BaseComponent, CompType, IndexerType
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.vector_stores.faiss import FaissVectorStore
from pydantic import model_serializer


class VectorIndexer(BaseComponent, VectorStoreIndex):

    def __init__(self, embed_model, vector_type):
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
        self._initialize_indexer(embed_model, vector_type)

    def _initialize_indexer(self, embed_model, vector_type):
        match vector_type:
            case IndexerType.DEFAULT_VECTOR:
                VectorStoreIndex.__init__(self, embed_model=embed_model, nodes=[])
            case IndexerType.FAISS_VECTOR:
                if embed_model:
                    d = embed_model._model.request.outputs[0].get_partial_shape()[2].get_length()
                else:
                    d = 128
                faiss_index = faiss.IndexFlatL2(d)
                faiss_store = StorageContext.from_defaults(vector_store=FaissVectorStore(faiss_index=faiss_index))
                VectorStoreIndex.__init__(self, embed_model=embed_model, nodes=[], storage_context=faiss_store)

    def reinitialize_indexer(self):
        if self.comp_subtype == IndexerType.FAISS_VECTOR:
            self._initialize_indexer(self.model, IndexerType.FAISS_VECTOR)

    def run(self, **kwargs) -> Any:
        pass

    @model_serializer
    def ser_model(self):
        set = {"idx": self.idx, "indexer_type": self.comp_subtype, "model": self.model}
        return set

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

# Embedding model
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Qdrant configuration
QDRANT_HOST = os.getenv("QDRANT", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "rag-qdrant")

# LLM/Embedding endpoints
TGI_LLM_ENDPOINT = os.getenv("TGI_LLM_ENDPOINT", "http://localhost:8080")
TGI_LLM_ENDPOINT_NO_RAG = os.getenv("TGI_LLM_ENDPOINT_NO_RAG", "http://localhost:8081")
TEI_EMBEDDING_ENDPOINT = os.getenv("TEI_ENDPOINT")

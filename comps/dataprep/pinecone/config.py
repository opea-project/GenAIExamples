# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

# Embedding model
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Pinecone configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "xxx_xxx")
PINECONE_INDEX_NAME = int(os.getenv("PINECONE_INDEX_NAME", "langchain-test"))

# LLM/Embedding endpoints
TGI_LLM_ENDPOINT = os.getenv("TGI_LLM_ENDPOINT", "http://localhost:8080")
TGI_LLM_ENDPOINT_NO_RAG = os.getenv("TGI_LLM_ENDPOINT_NO_RAG", "http://localhost:8081")
TEI_EMBEDDING_ENDPOINT = os.getenv("TEI_ENDPOINT")

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

# Neo4J configuration
NEO4J_URL = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "test")

# LLM/Embedding endpoints
TGI_LLM_ENDPOINT = os.getenv("TGI_LLM_ENDPOINT", "http://localhost:8080")
TGI_LLM_ENDPOINT_NO_RAG = os.getenv("TGI_LLM_ENDPOINT_NO_RAG", "http://localhost:8081")
TEI_EMBEDDING_ENDPOINT = os.getenv("TEI_ENDPOINT")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

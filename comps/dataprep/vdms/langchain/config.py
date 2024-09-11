# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os


def getEnv(key, default_value=None):
    env_value = os.getenv(key, default=default_value)
    print(f"{key}: {env_value}")
    return env_value


# Embedding model
EMBED_MODEL = getEnv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")

# VDMS configuration
VDMS_HOST = getEnv("VDMS_HOST", "localhost")
VDMS_PORT = int(getEnv("VDMS_PORT", 55555))
COLLECTION_NAME = getEnv("COLLECTION_NAME", "rag-vdms")
SEARCH_ENGINE = getEnv("SEARCH_ENGINE", "FaissFlat")
DISTANCE_STRATEGY = getEnv("DISTANCE_STRATEGY", "L2")

# LLM/Embedding endpoints
TGI_LLM_ENDPOINT = getEnv("TGI_LLM_ENDPOINT", "http://localhost:8080")
TGI_LLM_ENDPOINT_NO_RAG = getEnv("TGI_LLM_ENDPOINT_NO_RAG", "http://localhost:8081")
TEI_EMBEDDING_ENDPOINT = getEnv("TEI_ENDPOINT")

# chunk parameters
CHUNK_SIZE = getEnv("CHUNK_SIZE", 1500)
CHUNK_OVERLAP = getEnv("CHUNK_OVERLAP", 100)

current_file_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(current_file_path)

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

# Embedding model

EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")

PG_CONNECTION_STRING = os.getenv("PG_CONNECTION_STRING", "localhost")

# Vector Index Configuration
INDEX_NAME = os.getenv("INDEX_NAME", "rag-pgvector")

current_file_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(current_file_path)
PORT = os.getenv("RETRIEVER_PORT", 7000)

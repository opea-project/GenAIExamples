# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

ES_CONNECTION_STRING = os.getenv("ES_CONNECTION_STRING", "http://localhost:9200")
UPLOADED_FILES_PATH = os.getenv("UPLOADED_FILES_PATH", "./uploaded_files/")

# Embedding model
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")

# TEI Embedding endpoints
TEI_ENDPOINT = os.getenv("TEI_ENDPOINT", "")

# Vector Index Configuration
INDEX_NAME = os.getenv("INDEX_NAME", "rag-elastic")

# chunk parameters
CHUNK_SIZE = os.getenv("CHUNK_SIZE", 1500)
CHUNK_OVERLAP = os.getenv("CHUNK_OVERLAP", 100)

# Logging enabled
LOG_FLAG = os.getenv("LOGFLAG", False)

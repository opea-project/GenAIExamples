# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

# Embedding model
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")

ES_CONNECTION_STRING = os.getenv("ES_CONNECTION_STRING", "http://localhost:9200")

# TEI Embedding endpoints
TEI_ENDPOINT = os.getenv("TEI_ENDPOINT", "")

# Vector Index Configuration
INDEX_NAME = os.getenv("INDEX_NAME", "rag-elastic")

# Logging enabled
LOG_FLAG = os.getenv("LOGFLAG", False)

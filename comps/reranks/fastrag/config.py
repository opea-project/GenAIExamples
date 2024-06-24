# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

# Re-ranking model
RANKER_MODEL = os.getenv("EMBED_MODEL", "Intel/bge-small-en-v1.5-rag-int8-static")

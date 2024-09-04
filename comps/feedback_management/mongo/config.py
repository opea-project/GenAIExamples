# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

# MONGO configuration
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", 27017)
DB_NAME = os.getenv("DB_NAME", "OPEA")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "Feedback")

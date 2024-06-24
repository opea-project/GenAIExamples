#!/bin/sh

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

cd /home/user/comps/retrievers/langchain/pgvector
python ingest.py

python retriever_pgvector.py

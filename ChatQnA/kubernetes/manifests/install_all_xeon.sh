#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Array of YAML file names
yaml_files=("qna_configmap_xeon" "redis-vector-db"  "tei_embedding_service" "tei_reranking_service" "tgi_service" "retriever" "embedding" "reranking" "llm" "chaqna-xeon-backend-server")
for element in ${yaml_files[@]}
do
    echo "Applying manifest from ${element}.yaml"
    kubectl apply -f "${element}.yaml"
done

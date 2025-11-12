#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
if ls *.json 1> /dev/null 2>&1; then
    rm *.json
fi
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/visualqna_megaservice_grafana.json
if [ $? -ne 0 ]; then
    echo "Error: Failed to download visualqna_megaservice_grafana.json"
    exit 1
fi
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/vllm_grafana.json
if [ $? -ne 0 ]; then
    echo "Error: Failed to download vllm_grafana.json"
    exit 1
fi
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/tgi_grafana.json
if [ $? -ne 0 ]; then
    echo "Error: Failed to download tgi_grafana.json"
    exit 1
fi
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/node_grafana.json
if [ $? -ne 0 ]; then
    echo "Error: Failed to download node_grafana.json"
    exit 1
fi

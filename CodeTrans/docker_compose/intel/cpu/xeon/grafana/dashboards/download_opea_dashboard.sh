#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
if ls *.json 1> /dev/null 2>&1; then
    rm *.json
fi

wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/vllm_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/tgi_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/codetrans_megaservice_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/node_grafana.json

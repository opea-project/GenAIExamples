#!/bin/bash

# Copyright (C) 2025 Advanced Micro Devices, Inc.
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
if ls ./*.json 1>/dev/null 2>&1; then
	rm ./*.json
fi
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/chatqna_megaservice_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/qdrant_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/milvus_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/redis_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/tei_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/vllm_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/tgi_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/node_grafana.json

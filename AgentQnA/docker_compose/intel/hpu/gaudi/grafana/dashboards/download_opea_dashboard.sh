# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

rm *.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/chatqna_megaservice_grafana.json
mv chatqna_megaservice_grafana.json agentqna_microervices_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/vllm_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/tgi_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/node_grafana.json
wget https://raw.githubusercontent.com/opea-project/GenAIEval/refs/heads/main/evals/benchmark/grafana/gaudi_grafana.json

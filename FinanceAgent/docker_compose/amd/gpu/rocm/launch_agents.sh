# Copyright (C) 2025 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

export ip_address=$(hostname -I | awk '{print $1}')
export HOST_IP=${ip_address}
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export TOOLSET_PATH=$WORKDIR/GenAIExamples/FinanceAgent/tools/
echo "TOOLSET_PATH=${TOOLSET_PATH}"
export PROMPT_PATH=$WORKDIR/GenAIExamples/FinanceAgent/prompts/
echo "PROMPT_PATH=${PROMPT_PATH}"
export recursion_limit_worker=12
export recursion_limit_supervisor=10

export vllm_port=8086
export FINANCEAGENT_VLLM_SERVICE_PORT=${vllm_port}
export LLM_MODEL_ID="meta-llama/Llama-3.3-70B-Instruct"
export LLM_ENDPOINT_URL="http://${ip_address}:${vllm_port}"
export TEMPERATURE=0.5
export MAX_TOKENS=4096

export WORKER_FINQA_AGENT_URL="http://${ip_address}:9095/v1/chat/completions"
export WORKER_RESEARCH_AGENT_URL="http://${ip_address}:9096/v1/chat/completions"

export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:10221"
export REDIS_URL_VECTOR="redis://${ip_address}:6379"
export REDIS_URL_KV="redis://${ip_address}:6380"

export MAX_INPUT_TOKENS=2048
export MAX_TOTAL_TOKENS=4096
export DOCSUM_COMPONENT_NAME="OpeaDocSumvLLM"
export DOCSUM_ENDPOINT="http://${ip_address}:9000/v1/docsum"

export FINNHUB_API_KEY=${FINNHUB_API_KEY}
export FINANCIAL_DATASETS_API_KEY=${FINANCIAL_DATASETS_API_KEY}

docker compose -f compose.yaml up -d

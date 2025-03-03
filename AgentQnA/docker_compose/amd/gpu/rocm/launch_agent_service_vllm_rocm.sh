# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

export ip_address=${host_ip}

export WORKPATH=$(dirname "$PWD")
export WORKDIR=${WORKPATH}/../../../../
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export VLLM_SERVICE_PORT="8081"
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export VLLM_LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"

export HF_CACHE_DIR="./data"

export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/
export WORKER_RAG_AGENT_PORT="9095"
export recursion_limit_worker=12
export LLM_ENDPOINT_URL=http://${ip_address}:${VLLM_SERVICE_PORT}
export LLM_MODEL_ID=${VLLM_LLM_MODEL_ID}
export temperature=0.01
export max_new_tokens=512
export RETRIEVAL_TOOL_URL="http://${ip_address}:8889/v1/retrievaltool"
export LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
export LANGCHAIN_TRACING_V2=${LANGCHAIN_TRACING_V2}

export WORKER_SQL_AGENT_PORT="9096"
export db_name=Chinook
export db_path="sqlite:////home/user/chinook-db/Chinook_Sqlite.sqlite"
export recursion_limit_worker=12

export SUPERVISOR_REACT_AGENT_PORT="9090"
export recursion_limit_supervisor=10
export CRAG_SERVER_PORT="18881"
export CRAG_SERVER=http://${ip_address}:${CRAG_SERVER_PORT}
export WORKER_AGENT_URL="http://${ip_address}:${WORKER_RAG_AGENT_PORT}/v1/chat/completions"
export SQL_AGENT_URL="http://${ip_address}:${WORKER_SQL_AGENT_PORT}/v1/chat/completions"

bash ../../../../retrieval_tool/launch_retrieval_tool.sh

docker compose -f compose_vllm.yaml up -d

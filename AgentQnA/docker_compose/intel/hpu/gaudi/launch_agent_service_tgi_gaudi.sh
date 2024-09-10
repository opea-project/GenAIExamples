# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

WORKPATH=$(dirname "$PWD")/..
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

# LLM related environment variables
export HF_CACHE_DIR=${HF_CACHE_DIR}
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-70B-Instruct"
export NUM_SHARDS=4
export LLM_ENDPOINT_URL="http://${ip_address}:8085"
export temperature=0.01
export max_new_tokens=512

# agent related environment variables
export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/
export recursion_limit_worker=12
export recursion_limit_supervisor=10
export WORKER_AGENT_URL="http://${ip_address}:9095/v1/chat/completions"
export RETRIEVAL_TOOL_URL="http://${ip_address}:8889/v1/retrievaltool"
export CRAG_SERVER=http://${ip_address}:8080

docker compose -f compose.yaml up -d

sleep 5s
echo "Waiting tgi gaudi ready"
n=0
until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
    docker logs tgi-server &> ${WORKPATH}/tests/tgi-gaudi-service.log
    n=$((n+1))
    if grep -q Connected ${WORKPATH}/tests/tgi-gaudi-service.log; then
        break
    fi
    sleep 5s
done
sleep 5s
echo "Service started successfully"

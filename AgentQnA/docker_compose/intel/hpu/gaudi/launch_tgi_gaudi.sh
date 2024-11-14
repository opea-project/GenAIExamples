# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# LLM related environment variables
export HF_CACHE_DIR=${HF_CACHE_DIR}
ls $HF_CACHE_DIR
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-70B-Instruct"
export NUM_SHARDS=4

docker compose -f tgi_gaudi.yaml up -d

sleep 5s
echo "Waiting tgi gaudi ready"
n=0
until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
    docker logs tgi-server &> tgi-gaudi-service.log
    n=$((n+1))
    if grep -q Connected tgi-gaudi-service.log; then
        break
    fi
    sleep 5s
done
sleep 5s
echo "Service started successfully"

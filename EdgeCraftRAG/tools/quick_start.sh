#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$(pwd)")

get_user_input() {
    local var_name=$1
    local default_value=$2
    read -p "To set ${var_name} as [${default_value}], press Enter to confirm, or type a new value: " user_input
    echo ${user_input:-$default_value}
}

get_enable_function() {
    local var_name=$1
    local default_value=$2
    read -p "Do you want to enable ${var_name} [${default_value}]: " user_input
    echo ${user_input:-$default_value}
}

function start_vllm_services() {
    COMPOSE_FILE="compose_vllm.yaml"
    echo "stop former service..."
    docker compose -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE down

    ip_address=$(hostname -I | awk '{print $1}')
    HOST_IP=$(get_user_input "host ip" "${ip_address}")
    DOC_PATH=$(get_user_input "DOC_PATH" "$WORKPATH/tests")
    TMPFILE_PATH=$(get_user_input "TMPFILE_PATH" "$WORKPATH/tests")
    MILVUS_ENABLED=$(get_enable_function "MILVUS DB(Enter 1 for enable)" "0")
    CHAT_HISTORY_ROUND=$(get_user_input "chat history round" "0")
    LLM_MODEL=$(get_user_input "your LLM model" "Qwen/Qwen3-8B")
    MODEL_PATH=$(get_user_input "your model path" "${HOME}/models")
    read -p "Have you prepare models in ${MODEL_PATH}:(yes/no) [yes]" user_input
    user_input=${user_input:-"yes"}

    if [ "$user_input" == "yes" ]; then
        # 模型文件路径请参考以下形式存放， llm为huggingface
        # Indexer: ${MODEL_PATH}/BAAI/bge-small-en-v1.5
        # Reranker: ${MODEL_PATH}/BAAI/bge-reranker-large
        # llm :${MODEL_PATH}/${LLM_MODEL} (从huggingface或modelscope下载的原始模型，而不是经过OpenVINO转换的模型!)
        echo "you skipped model downloading, please make sure you have prepared all models under ${MODEL_PATH}"
    else
        echo "you have not prepare models, starting to download models into ${MODEL_PATH}..."
        mkdir -p $MODEL_PATH
        pip install --upgrade --upgrade-strategy eager "optimum[openvino]"
        optimum-cli export openvino -m BAAI/bge-small-en-v1.5 ${MODEL_PATH}/BAAI/bge-small-en-v1.5 --task sentence-similarity
        optimum-cli export openvino -m BAAI/bge-reranker-large ${MODEL_PATH}/BAAI/bge-reranker-large --task text-classification
        pip install -U huggingface_hub
        huggingface-cli download $LLM_MODEL --local-dir "${MODEL_PATH}/${LLM_MODEL}"
    fi
    echo "give permission to related path..."
    sudo chown 1000:1000 ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
    sudo chown -R 1000:1000 ${HOME}/.cache/huggingface
    HF_ENDPOINT=https://hf-mirror.com
    # vllm ENV
    export NGINX_PORT=8086
    export vLLM_ENDPOINT="http://${HOST_IP}:${NGINX_PORT}"
    TENSOR_PARALLEL_SIZE=$(get_user_input "your tp size" 1)
    SELECTED_XPU_0=$(get_user_input "selected GPU " "0")
    DP_NUM=$(get_user_input "DP number(how many containers to run vLLM)" 1)
    for (( x=0; x<DP_NUM; x++ ))
    do
        export VLLM_SERVICE_PORT_${x}="8$((x+1))00"
        export SELECTED_XPU_${x}=$x
    done
    export HOST_IP=${HOST_IP}
    export VLLM_SERVICE_PORT_0=8100
    # export ENV
    export MODEL_PATH=${MODEL_PATH}
    export DOC_PATH=${DOC_PATH}
    export TMPFILE_PATH=${TMPFILE_PATH}
    export LLM_MODEL=${LLM_MODEL}
    export HF_ENDPOINT=${HF_ENDPOINT}
    export no_proxy="localhost, 127.0.0.1, 192.168.1.1, ${HOST_IP}"
    export MILVUS_ENABLED=${MILVUS_ENABLED}
    export CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND}
    export SELECTED_XPU_0=${SELECTED_XPU_0}
    export TENSOR_PARALLEL_SIZE=${TENSOR_PARALLEL_SIZE}

    bash $WORKPATH/nginx/nginx-conf-generator.sh $DP_NUM $WORKPATH/nginx/nginx.conf
    export NGINX_CONFIG_PATH="${WORKPATH}/nginx/nginx.conf"

    # Start Docker Containers
    bash $WORKPATH/docker_compose/intel/gpu/arc/multi-arc-yaml-generator.sh $DP_NUM $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE
    docker compose -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE up -d
    echo "ipex-llm-serving-xpu is booting, please wait..."
    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs ipex-llm-serving-xpu-container-0 > ipex-llm-serving-xpu-container.log 2>&1
        if grep -q "Starting vLLM API server on http://0.0.0.0:" ipex-llm-serving-xpu-container.log; then
            break
        fi
        sleep 6s
        n=$((n+1))
    done
    rm -rf ipex-llm-serving-xpu-container.log
    echo "service launched, please visit UI at ${HOST_IP}:8082"
}


function start_services() {
    COMPOSE_FILE="compose.yaml"
    echo "stop former service..."
    docker compose -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE down

    ip_address=$(hostname -I | awk '{print $1}')
    HOST_IP=$(get_user_input "host ip" "${ip_address}")
    DOC_PATH=$(get_user_input "DOC_PATH" "$WORKPATH/tests")
    TMPFILE_PATH=$(get_user_input "TMPFILE_PATH" "$WORKPATH/tests")
    MILVUS_ENABLED=$(get_enable_function "MILVUS DB(Enter 1 for enable)" "0")
    CHAT_HISTORY_ROUND=$(get_user_input "chat history round" "0")
    LLM_MODEL=$(get_user_input "your LLM model" "Qwen/Qwen3-8B")
    MODEL_PATH=$(get_user_input "your model path" "${HOME}/models")
    read -p "Have you prepare models in ${MODEL_PATH}:(yes/no) [yes]" user_input
    user_input=${user_input:-"yes"}

    if [ "$user_input" == "yes" ]; then
        # 模型文件路径请参考以下形式存放
        # Indexer: ${MODEL_PATH}/BAAI/bge-small-en-v1.5
        # Reranker: ${MODEL_PATH}/BAAI/bge-reranker-large
        # llm :${MODEL_PATH}/${LLM_MODEL}/INT4_compressed_weights
        echo "you skipped model downloading, please make sure you have prepared all models under ${MODEL_PATH}"
    else
        read -p "you have not prepare models, do you need one-click model downloading into ${MODEL_PATH}:(yes/no) [yes]" your_input
        your_input=${your_input:-"yes"}
        if [ "$your_input" == "yes" ]; then
            echo "start to download models..."
            mkdir -p $MODEL_PATH
            pip install --upgrade --upgrade-strategy eager "optimum[openvino]"
            optimum-cli export openvino -m BAAI/bge-small-en-v1.5 ${MODEL_PATH}/BAAI/bge-small-en-v1.5 --task sentence-similarity
            optimum-cli export openvino -m BAAI/bge-reranker-large ${MODEL_PATH}/BAAI/bge-reranker-large --task text-classification
            optimum-cli export openvino --model ${LLM_MODEL} ${MODEL_PATH}/${LLM_MODEL}/INT4_compressed_weights --task text-generation-with-past --weight-format int4 --group-size 128 --ratio 0.8
        else
            echo "Please prepare models before launch service..."
            exit 0
        fi
    fi
    echo "give permission to related path..."
    sudo chown 1000:1000 ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
    sudo chown -R 1000:1000 ${HOME}/.cache/huggingface
    HF_ENDPOINT=https://hf-mirror.com

    # export ENV
    export MODEL_PATH=${MODEL_PATH}
    export DOC_PATH=${DOC_PATH}
    export TMPFILE_PATH=${TMPFILE_PATH}
    export HOST_IP=${HOST_IP}
    export LLM_MODEL=${LLM_MODEL}
    export HF_ENDPOINT=${HF_ENDPOINT}
    export no_proxy="localhost, 127.0.0.1, 192.168.1.1, ${HOST_IP}"
    export MILVUS_ENABLED=${MILVUS_ENABLED}
    export CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND}

    # Start Docker Containers
    COMPOSE_FILE="compose.yaml"
    echo "starting service..."
    docker compose -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE up -d
}

function main {
    read -p "Do you want to start vLLM or local OpenVINO services? (vLLM/ov) [vLLM]: " user_input
    user_input=${user_input:-"vLLM"}

    if [ "$user_input" == "vLLM" ]; then
        start_vllm_services
    else
        start_services
    fi
}

main

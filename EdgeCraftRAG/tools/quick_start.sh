#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
WORKPATH=$(cd "${SCRIPT_DIR}/.." && pwd)
ip_address=$(hostname -I | awk '{print $1}')
HOST_IP=$ip_address

# global defaults to avoid docker compose warnings on unset variables
export HOST_IP=${HOST_IP:-"${ip_address}"}
export MODEL_PATH=${MODEL_PATH:-"${WORKPATH}/workspace/models"}
export LLM_MODEL=${LLM_MODEL:-"Qwen/Qwen3-8B"}
export DOC_PATH=${DOC_PATH:-"${WORKPATH}/workspace"}
export TMPFILE_PATH=${TMPFILE_PATH:-"${WORKPATH}/workspace"}
export MILVUS_ENABLED=${MILVUS_ENABLED:-"0"}
export CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND:-"0"}

#use python venv
ENV_NAME="${WORKPATH}/ecrag_venv"

# check if python3-venv (ensurepip) is fully available; install if missing
if ! python3 -c "import ensurepip" &>/dev/null; then
    echo "python3-venv (ensurepip) not found, installing..."
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y "python${PY_VER}-venv"
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-virtualenv
    elif command -v yum &>/dev/null; then
        sudo yum install -y python3-virtualenv
    else
        echo "ERROR: Cannot install python3-venv: unsupported package manager. Please install it manually."
        exit 1
    fi
fi

# create venv if missing or broken (activate script absent)
if [ ! -f "${ENV_NAME}/bin/activate" ] && [ ! -f "${ENV_NAME}/Scripts/activate" ]; then
    echo "Creating virtual environment at ${ENV_NAME}..."
    rm -rf "${ENV_NAME}"
    python3 -m venv "${ENV_NAME}"
fi

# activate venv
if [ -f "${ENV_NAME}/bin/activate" ]; then
    source "${ENV_NAME}/bin/activate"
elif [ -f "${ENV_NAME}/Scripts/activate" ]; then
    source "${ENV_NAME}/Scripts/activate"
else
    echo "ERROR: Failed to activate virtual environment at ${ENV_NAME}"
    exit 1
fi

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

print_ui_access_info() {
    echo ""
    echo "Service launched successfully."
    echo "UI access URL: http://${HOST_IP}:8082"
    echo "If you are accessing from another machine, replace ${HOST_IP} with the server's reachable IP or hostname."
}

function start_vllm_services() {
    COMPOSE_FILE="compose.yaml"
    echo "stop former service..."
    docker compose -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE down

    ip_address=$(hostname -I | awk '{print $1}')
    HOST_IP=$(get_user_input "host ip" "${ip_address}")
    DOC_PATH=$(get_user_input "DOC_PATH" "$WORKPATH/workspace")
    TMPFILE_PATH=$(get_user_input "TMPFILE_PATH" "$WORKPATH/workspace")
    MILVUS_ENABLED=$(get_enable_function "MILVUS DB(Enter 1 for enable)" "0")
    CHAT_HISTORY_ROUND=$(get_user_input "chat history round" "0")
    LLM_MODEL=$(get_user_input "your LLM model" "Qwen/Qwen3-8B")
    MODEL_PATH=$(get_user_input "your model path" "${WORKPATH}/workspace/models")
    read -p "Have you prepare models in ${MODEL_PATH}:(yes/no) [yes]" user_input
    user_input=${user_input:-"yes"}

    if [ "$user_input" == "yes" ]; then
        # 模型文件路径请参考以下形式存放， llm为huggingface
        # Indexer: ${MODEL_PATH}/BAAI/bge-small-en-v1.5
        # Reranker: ${MODEL_PATH}/BAAI/bge-reranker-large
        # llm :${MODEL_PATH}/${LLM_MODEL} (从huggingface或modelscope下载的原始模型，而不是经过OpenVINO转换的模型!)
        echo "you skipped model downloading, please make sure you have prepared all models under ${MODEL_PATH}"
        ensure_required_models_for_vllm
    else
        echo "you have not prepare models, starting to download models into ${MODEL_PATH}..."
        mkdir -p $MODEL_PATH
        python -m pip install --upgrade-strategy eager "optimum-intel[openvino]"
        optimum-cli export openvino -m BAAI/bge-small-en-v1.5 ${MODEL_PATH}/BAAI/bge-small-en-v1.5 --task sentence-similarity
        optimum-cli export openvino -m BAAI/bge-reranker-large ${MODEL_PATH}/BAAI/bge-reranker-large --task text-classification
        pip install huggingface_hub
        huggingface-cli download $LLM_MODEL --local-dir "${MODEL_PATH}/${LLM_MODEL}"
    fi
    HF_CACHE="${HOME}/.cache"
    if [ ! -d "${HF_CACHE}" ]; then
        mkdir -p "${HF_CACHE}"
        echo "Created directory: ${HF_CACHE}"
    fi
    echo "give permission to related path..."
    sudo chown 1000:1000 ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
    sudo chown -R 1000:1000 ${HF_CACHE}
    HF_ENDPOINT=https://hf-mirror.com
    # vllm ENV
    export VLLM_SERVICE_PORT_A770=8086

    read -p "Tensor parallel size(your tp size [1]), press Enter to confirm, or type a new value:" TENSOR_PARALLEL_SIZE; TP=${TP:-1}
    CCL_DG2_USM=$(get_user_input "Set USM (Core=1, Xeon=0, default=0)" 0)
    export HOST_IP=${HOST_IP}
    # export ENV
    export MODEL_PATH=${MODEL_PATH}
    export DOC_PATH=${DOC_PATH}
    export TMPFILE_PATH=${TMPFILE_PATH}
    export LLM_MODEL=${LLM_MODEL}
    export HF_ENDPOINT=${HF_ENDPOINT}
    export no_proxy="localhost, 127.0.0.1, 192.168.1.1, ${HOST_IP}"
    export MILVUS_ENABLED=${MILVUS_ENABLED}
    export CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND}
    export TP=${TP}
    export CCL_DG2_USM=${CCL_DG2_USM}
    export VIDEOGROUPID=$(getent group video | cut -d: -f3)
    export RENDERGROUPID=$(getent group render | cut -d: -f3)


    # Start Docker Containers
    docker compose --profile a770 -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE up -d
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
    print_ui_access_info
}


function start_services() {
    COMPOSE_FILE="compose.yaml"
    echo "stop former service..."
    docker compose -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE down

    ip_address=$(hostname -I | awk '{print $1}')
    HOST_IP=$(get_user_input "host ip" "${ip_address}")
    DOC_PATH=$(get_user_input "DOC_PATH" "$WORKPATH/workspace")
    TMPFILE_PATH=$(get_user_input "TMPFILE_PATH" "$WORKPATH/workspace")
    MILVUS_ENABLED=$(get_enable_function "MILVUS DB(Enter 1 for enable)" "0")
    CHAT_HISTORY_ROUND=$(get_user_input "chat history round" "0")
    LLM_MODEL=$(get_user_input "your LLM model" "Qwen/Qwen3-8B")
    MODEL_PATH=$(get_user_input "your model path" "${WORKPATH}/workspace/models")
    read -p "Have you prepare models in ${MODEL_PATH}:(yes/no) [yes]" user_input
    user_input=${user_input:-"yes"}

    if [ "$user_input" == "yes" ]; then
        # 模型文件路径请参考以下形式存放
        # Indexer: ${MODEL_PATH}/BAAI/bge-small-en-v1.5
        # Reranker: ${MODEL_PATH}/BAAI/bge-reranker-large
        # llm :${MODEL_PATH}/${LLM_MODEL}/INT4_compressed_weights
        echo "you skipped model downloading, please make sure you have prepared all models under ${MODEL_PATH}"
        ensure_required_models_for_ov
    else
        read -p "you have not prepare models, do you need one-click model downloading into ${MODEL_PATH}:(yes/no) [yes]" your_input
        your_input=${your_input:-"yes"}
        if [ "$your_input" == "yes" ]; then
            echo "start to download models..."
            mkdir -p $MODEL_PATH
            python -m pip install --upgrade-strategy eager "optimum-intel[openvino]"
            optimum-cli export openvino -m BAAI/bge-small-en-v1.5 ${MODEL_PATH}/BAAI/bge-small-en-v1.5 --task sentence-similarity
            optimum-cli export openvino -m BAAI/bge-reranker-large ${MODEL_PATH}/BAAI/bge-reranker-large --task text-classification
            optimum-cli export openvino --model ${LLM_MODEL} ${MODEL_PATH}/${LLM_MODEL}/INT4_compressed_weights --task text-generation-with-past --weight-format int4 --group-size 128 --ratio 0.8
        else
            echo "Please prepare models before launch service..."
            exit 0
        fi
    fi
    HF_CACHE="${HOME}/.cache"
    if [ ! -d "${HF_CACHE}" ]; then
        mkdir -p "${HF_CACHE}"
        echo "Created directory: ${HF_CACHE}"
    fi
    echo "give permission to related path..."
    sudo chown 1000:1000 ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
    sudo chown -R 1000:1000 ${HF_CACHE}
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
    export VIDEOGROUPID=$(getent group video | cut -d: -f3)
    export RENDERGROUPID=$(getent group render | cut -d: -f3)
    export MAX_MODEL_LEN=5000

    # Start Docker Containers
    COMPOSE_FILE="compose.yaml"
    echo "starting service..."
    docker compose -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE up -d
    print_ui_access_info
}


function check_baai_folder() {
    local baai_path="${MODEL_PATH}/BAAI"

    if [ -d "${baai_path}" ]; then
        return 0
    else
        echo "Error: BAAI folder not found in ${MODEL_PATH}!"
        echo "Please prepare the models first, then run quick_start_ov_services again."
        exit 1
    fi
}

ensure_openvino_tooling() {
    if ! command -v optimum-cli >/dev/null 2>&1; then
        echo "[Model Check] 'optimum-cli' not found, installing optimum-intel[openvino]..."
        python -m pip install --upgrade-strategy eager "optimum-intel[openvino]"
    fi
}

ensure_huggingface_tooling() {
    if ! command -v huggingface-cli >/dev/null 2>&1; then
        echo "[Model Check] 'huggingface-cli' not found, installing huggingface_hub..."
        python -m pip install huggingface_hub
    fi
}

ensure_embedding_and_reranker_models() {
    local embedding_dir="${MODEL_PATH}/BAAI/bge-small-en-v1.5"
    local reranker_dir="${MODEL_PATH}/BAAI/bge-reranker-large"

    if [ ! -f "${embedding_dir}/openvino_model.xml" ]; then
        echo "[Model Check] Embedding model missing: ${embedding_dir}"
        echo "[Model Check] Downloading embedding model..."
        ensure_openvino_tooling
        mkdir -p "${embedding_dir}"
        optimum-cli export openvino -m BAAI/bge-small-en-v1.5 "${embedding_dir}" --task sentence-similarity
    else
        echo "[Model Check] Embedding model exists: ${embedding_dir}"
    fi

    if [ ! -f "${reranker_dir}/openvino_model.xml" ]; then
        echo "[Model Check] Reranker model missing: ${reranker_dir}"
        echo "[Model Check] Downloading reranker model..."
        ensure_openvino_tooling
        mkdir -p "${reranker_dir}"
        optimum-cli export openvino -m BAAI/bge-reranker-large "${reranker_dir}" --task text-classification
    else
        echo "[Model Check] Reranker model exists: ${reranker_dir}"
    fi
}

ensure_llm_model_for_vllm() {
    local llm_dir="${MODEL_PATH}/${LLM_MODEL}"
    if [ ! -f "${llm_dir}/config.json" ]; then
        echo "[Model Check] vLLM LLM model missing: ${llm_dir}"
        echo "[Model Check] Downloading LLM model '${LLM_MODEL}'..."
        ensure_huggingface_tooling
        mkdir -p "${llm_dir}"
        huggingface-cli download "${LLM_MODEL}" --local-dir "${llm_dir}"
    else
        echo "[Model Check] vLLM LLM model exists: ${llm_dir}"
    fi
}

ensure_llm_model_for_ov() {
    local ov_llm_dir="${MODEL_PATH}/${LLM_MODEL}/INT4_compressed_weights"
    if [ ! -f "${ov_llm_dir}/openvino_model.xml" ]; then
        echo "[Model Check] OpenVINO LLM model missing: ${ov_llm_dir}"
        echo "[Model Check] Downloading and converting LLM model '${LLM_MODEL}' to INT4 OpenVINO..."
        ensure_openvino_tooling
        mkdir -p "${ov_llm_dir}"
        optimum-cli export openvino --model "${LLM_MODEL}" "${ov_llm_dir}" --task text-generation-with-past --weight-format int4 --group-size 128 --ratio 0.8
    else
        echo "[Model Check] OpenVINO LLM model exists: ${ov_llm_dir}"
    fi
}

ensure_required_models_for_vllm() {
    ensure_embedding_and_reranker_models
    ensure_llm_model_for_vllm
}

ensure_required_models_for_ov() {
    ensure_embedding_and_reranker_models
    ensure_llm_model_for_ov
}


function quick_start_vllm_services() {
    COMPOSE_FILE="compose.yaml"
    EC_RAG_SERVICE_PORT=16010
    docker compose -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE down

    ip_address=$(hostname -I | awk '{print $1}')
    export HOST_IP=${HOST_IP:-"${ip_address}"}
    export MODEL_PATH=${MODEL_PATH:-"${WORKPATH}/workspace/models"}
    export DOC_PATH=${DOC_PATH:-"$WORKPATH/workspace"}
    export TMPFILE_PATH=${TMPFILE_PATH:-"$WORKPATH/workspace"}
    export DP_NUM=${DP_NUM:-1}
    export MILVUS_ENABLED=${MILVUS_ENABLED:-1}
    export CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND:-2}
    export HF_ENDPOINT=${HF_ENDPOINT:-https://hf-mirror.com}
    export TP=${TP:-1}
    export MAX_NUM_SEQS=${MAX_NUM_SEQS:-64}
    export MAX_MODEL_LEN=${MAX_MODEL_LEN:-10240}
    export MAX_NUM_BATCHED_TOKENS=${MAX_NUM_BATCHED_TOKENS:-10240}
    export QUANTIZATION=${QUANTIZATION:-fp8}
    export CCL_DG2_USM=${CCL_DG2_USM:-0}
    export LLM_MODEL=${LLM_MODEL:-Qwen/Qwen3-8B}
    export LLM_MODEL_PATH=${LLM_MODEL_PATH:-"${MODEL_PATH}/${LLM_MODEL}"}
    export VIDEOGROUPID=$(getent group video | cut -d: -f3)
    export RENDERGROUPID=$(getent group render | cut -d: -f3)
    export VLLM_SERVICE_PORT_A770=8086

    ensure_required_models_for_vllm
    export HF_CACHE=${HF_CACHE:-"${HOME}/.cache"}
    export no_proxy="localhost, 127.0.0.1, 192.168.1.1, ${HOST_IP}"
    if [ ! -d "${HF_CACHE}" ]; then
        mkdir -p "${HF_CACHE}"
        echo "Created directory: ${HF_CACHE}"
    fi
    sudo chown -R 1000:1000 ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
    sudo chown -R 1000:1000 ${HF_CACHE}
    cd $WORKPATH/docker_compose/intel/gpu/arc

    docker compose --profile a770 -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE up -d
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
    print_ui_access_info
}


function quick_start_ov_services() {
    COMPOSE_FILE="compose.yaml"
    echo "stop former service..."
    docker compose -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE down

    ip_address=$(hostname -I | awk '{print $1}')
    export HOST_IP=${HOST_IP:-"${ip_address}"}
    export DOC_PATH=${DOC_PATH:-"$WORKPATH/workspace"}
    export TMPFILE_PATH=${TMPFILE_PATH:-"$WORKPATH/workspace"}
    export MILVUS_ENABLED=${MILVUS_ENABLED:-1}
    export CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND:-"0"}
    export LLM_MODEL=${LLM_MODEL:-"Qwen/Qwen3-8B"}
    export MODEL_PATH=${MODEL_PATH:-"${WORKPATH}/workspace/models"}
    export VIDEOGROUPID=$(getent group video | cut -d: -f3)
    export RENDERGROUPID=$(getent group render | cut -d: -f3)
    export MAX_MODEL_LEN=5000

    ensure_required_models_for_ov
    export HF_CACHE=${HF_CACHE:-"${HOME}/.cache"}
    if [ ! -d "${HF_CACHE}" ]; then
        mkdir -p "${HF_CACHE}"
        echo "Created directory: ${HF_CACHE}"
    fi

    sudo chown 1000:1000 "${MODEL_PATH}" "${DOC_PATH}" "${TMPFILE_PATH}"
    sudo chown -R 1000:1000 "${HF_CACHE}"
    export HF_ENDPOINT=${HF_ENDPOINT:-"https://hf-mirror.com"}
    export no_proxy="localhost, 127.0.0.1, 192.168.1.1, ${HOST_IP}"
    export CCL_DG2_USM=${CCL_DG2_USM:-0}

    echo "Starting service..."
    docker compose -f "$WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE" up -d
    print_ui_access_info
}


function start_vLLM_B60_services() {
    COMPOSE_FILE="compose.yaml"
    echo "stop former service..."
    export MODEL_PATH=${MODEL_PATH:-"${WORKPATH}/models"}
    docker compose -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE down

    ip_address=$(hostname -I | awk '{print $1}')
    HOST_IP=$(get_user_input "host ip" "${ip_address}")
    DOC_PATH=$(get_user_input "DOC_PATH" "$WORKPATH/workspace")
    TMPFILE_PATH=$(get_user_input "TMPFILE_PATH" "$WORKPATH/workspace")
    MILVUS_ENABLED=$(get_enable_function "MILVUS DB(Enter 1 for enable)" "0")
    CHAT_HISTORY_ROUND=$(get_user_input "chat history round" "0")
    LLM_MODEL=$(get_user_input "your LLM model" "Qwen/Qwen3-8B")
    MODEL_PATH=$(get_user_input "your model path" "${WORKPATH}/workspace/models")
    read -p "Have you prepare models in ${MODEL_PATH}:(yes/no) [yes]" user_input
    user_input=${user_input:-"yes"}

    if [ "$user_input" == "yes" ]; then
        # 模型文件路径请参考以下形式存放， llm为huggingface
        # Indexer: ${MODEL_PATH}/BAAI/bge-small-en-v1.5
        # Reranker: ${MODEL_PATH}/BAAI/bge-reranker-large
        # llm :${MODEL_PATH}/${LLM_MODEL} (从huggingface或modelscope下载的原始模型，而不是经过OpenVINO转换的模型!)
        echo "you skipped model downloading, please make sure you have prepared all models under ${MODEL_PATH}"
        ensure_required_models_for_vllm
    else
        echo "you have not prepare models, starting to download models into ${MODEL_PATH}..."
        mkdir -p $MODEL_PATH
        python -m pip install --upgrade-strategy eager "optimum-intel[openvino]"
        optimum-cli export openvino -m BAAI/bge-small-en-v1.5 ${MODEL_PATH}/BAAI/bge-small-en-v1.5 --task sentence-similarity
        optimum-cli export openvino -m BAAI/bge-reranker-large ${MODEL_PATH}/BAAI/bge-reranker-large --task text-classification
        pip install huggingface_hub
        huggingface-cli download $LLM_MODEL --local-dir "${MODEL_PATH}/${LLM_MODEL}"
    fi
    echo "give permission to related path..."
    sudo chown 1000:1000 ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
    # vllm ENV
    export VLLM_SERVICE_PORT_B60=8086
    export vLLM_ENDPOINT="http://${HOST_IP}:${VLLM_SERVICE_PORT_B60}"
    read -p "DP number(how many containers to run B60_vLLM) [4] , press Enter to confirm, or type a new value:" DP; DP=${DP:-4}
    read -p "Tensor parallel size(your tp size [1]), press Enter to confirm, or type a new value:" TP; TP=${TP:-1}
    DTYPE=$(get_user_input "DTYPE (vLLM data type, e.g. float16/bfloat16)" "float16")
    ZE_AFFINITY_MASK=$(get_user_input "ZE_AFFINITY_MASK (GPU affinity mask, multi-GPU use 0,1,2...)" "0,1,2,3")
    ENFORCE_EAGER=$(get_user_input "ENFORCE_EAGER (enable eager execution, 1=enable/0=disable)" "1")
    TRUST_REMOTE_CODE=$(get_user_input "TRUST_REMOTE_CODE (trust remote code for custom models, 1=enable/0=disable)" "1")
    DISABLE_SLIDING_WINDOW=$(get_user_input "DISABLE_SLIDING_WINDOW (disable sliding window attention, 1=disable/0=enable)" "1")
    GPU_MEMORY_UTIL=$(get_user_input "GPU_MEMORY_UTIL (GPU memory utilization, range 0.1-1.0)" "0.8")
    NO_ENABLE_PREFIX_CACHING=$(get_user_input "NO_ENABLE_PREFIX_CACHING (disable prefix caching, 1=disable/0=enable)" "1")
    MAX_NUM_BATCHED_TOKENS=$(get_user_input "MAX_NUM_BATCHED_TOKENS (max number of batched tokens)" "8192")
    DISABLE_LOG_REQUESTS=$(get_user_input "DISABLE_LOG_REQUESTS (disable request logs, 1=disable/0=enable)" "1")
    MAX_MODEL_LEN=$(get_user_input "MAX_MODEL_LEN (max model context length, e.g. 40000/10240)" "40000")
    BLOCK_SIZE=$(get_user_input "BLOCK_SIZE (vLLM block size)" "64")
    QUANTIZATION=$(get_user_input "QUANTIZATION (model quantization method, e.g. fp8/int4)" "fp8")
    # export ENV
    export HOST_IP=${HOST_IP:-"${ip_address}"}
    export MODEL_PATH=${MODEL_PATH}
    export DOC_PATH=${DOC_PATH}
    export TMPFILE_PATH=${TMPFILE_PATH}
    export LLM_MODEL=${LLM_MODEL}
    export no_proxy="localhost, 127.0.0.1, 192.168.1.1, ${HOST_IP}"
    export MILVUS_ENABLED=${MILVUS_ENABLED}
    export CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND}
    export ZE_AFFINITY_MASK=${ZE_AFFINITY_MASK}
    export VIDEOGROUPID=$(getent group video | cut -d: -f3)
    export RENDERGROUPID=$(getent group render | cut -d: -f3)
    # export vllm ENV
    export DP=${DP}
    export TP=${TP}
    export DTYPE=${DTYPE}
    export ZE_AFFINITY_MASK=${ZE_AFFINITY_MASK}
    export ENFORCE_EAGER=${ENFORCE_EAGER}
    export TRUST_REMOTE_CODE=${TRUST_REMOTE_CODE}
    export DISABLE_SLIDING_WINDOW=${DISABLE_SLIDING_WINDOW}
    export GPU_MEMORY_UTIL=${GPU_MEMORY_UTIL}
    export NO_ENABLE_PREFIX_CACHING=${NO_ENABLE_PREFIX_CACHING}
    export MAX_NUM_BATCHED_TOKENS=${MAX_NUM_BATCHED_TOKENS}
    export DISABLE_LOG_REQUESTS=${DISABLE_LOG_REQUESTS}
    export MAX_MODEL_LEN=${MAX_MODEL_LEN}
    export BLOCK_SIZE=${BLOCK_SIZE}
    export QUANTIZATION=${QUANTIZATION}

    # Start Docker Containers
    docker compose --profile b60 -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE up -d
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
    print_ui_access_info
}


function quick_start_vllm_B60_services() {
    COMPOSE_FILE="compose.yaml"
    EC_RAG_SERVICE_PORT=16010
    docker compose -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE down

    ip_address=$(hostname -I | awk '{print $1}')
    export HOST_IP=${HOST_IP:-"${ip_address}"}
    export MODEL_PATH=${MODEL_PATH:-"${WORKPATH}/workspace/models"}
    export DOC_PATH=${DOC_PATH:-"$WORKPATH/workspace"}
    export TMPFILE_PATH=${TMPFILE_PATH:-"$WORKPATH/workspace"}
    export MILVUS_ENABLED=${MILVUS_ENABLED:-1}
    export CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND:-2}
    export LLM_MODEL=${LLM_MODEL:-Qwen/Qwen3-8B}
    export VIDEOGROUPID=$(getent group video | cut -d: -f3)
    export RENDERGROUPID=$(getent group render | cut -d: -f3)
    # export vllm ENV
    export DP=${DP:-1}
    export TP=${TP:-1}
    export DTYPE=${DTYPE:-float16}
    export ZE_AFFINITY_MASK=${ZE_AFFINITY_MASK:-0}
    export ENFORCE_EAGER=${ENFORCE_EAGER:-1}
    export TRUST_REMOTE_CODE=${TRUST_REMOTE_CODE:-1}
    export DISABLE_SLIDING_WINDOW=${DISABLE_SLIDING_WINDOW:-1}
    export GPU_MEMORY_UTIL=${GPU_MEMORY_UTIL:-0.8}
    export NO_ENABLE_PREFIX_CACHING=${NO_ENABLE_PREFIX_CACHING:-1}
    export MAX_NUM_BATCHED_TOKENS=${MAX_NUM_BATCHED_TOKENS:-8192}
    export DISABLE_LOG_REQUESTS=${disable_LOG_REQUESTS:-1}
    export MAX_MODEL_LEN=${MAX_MODEL_LEN:-40000}
    export BLOCK_SIZE=${BLOCK_SIZE:-64}
    export QUANTIZATION=${QUANTIZATION:-fp8}


    ensure_required_models_for_vllm
    export no_proxy="localhost, 127.0.0.1, 192.168.1.1, ${HOST_IP}"
    sudo chown -R 1000:1000 ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
    docker compose --profile b60 -f $WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE up -d
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
    print_ui_access_info
}


function quick_cleanup_services() {
    COMPOSE_FILE="compose.yaml"
    echo "Stopping EdgeCraftRAG services..."
    docker compose -f "$WORKPATH/docker_compose/intel/gpu/arc/$COMPOSE_FILE" down
    echo "Cleanup completed."
}


function main {
    if [[ "${1:-}" == "cleanup" ]]; then
        quick_cleanup_services
        exit 0
    fi

    if [[ $- == *i* ]]; then
        read -p "Do you want to start vLLM or local OpenVINO services? (vLLM_A770/vLLM_B60/ov) [ov]: " user_input
        user_input=${user_input:-"ov"}
        if [[ "$user_input" == "vLLM_A770" ]]; then
            start_vllm_services
        elif [[ "$user_input" == "vLLM_B60" ]]; then
            start_vLLM_B60_services
        else
            start_services
        fi
    else
        export COMPOSE_PROFILES=${COMPOSE_PROFILES:-""}
        if [[ "$COMPOSE_PROFILES" == "vLLM_A770" || "$COMPOSE_PROFILES" == "vLLM"  || "$COMPOSE_PROFILES" == "vllm_on_a770" ]]; then
            quick_start_vllm_services
        elif [[ "$COMPOSE_PROFILES" == "vLLM_B60" || "$COMPOSE_PROFILES" == "vLLM_b60" || "$COMPOSE_PROFILES" == "vllm_on_b60" ]]; then
            quick_start_vllm_B60_services
        else
            quick_start_ov_services
        fi
    fi
}

main

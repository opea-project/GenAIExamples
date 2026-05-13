#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# EdgeCraftRAG Model Download Tool
# Supports ModelScope (default) and Hugging Face download sources.

set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
WORKPATH=$(cd "${SCRIPT_DIR}/.." && pwd)
ENV_NAME="${WORKPATH}/ecrag_venv"

MODEL_PATH=${MODEL_PATH:-"${WORKPATH}/workspace/models"}
LLM_MODEL=${LLM_MODEL:-"Qwen/Qwen3-8B"}
EMBEDDING_MODEL=${EMBEDDING_MODEL:-"BAAI/bge-small-en-v1.5"}
RERANKER_MODEL=${RERANKER_MODEL:-"BAAI/bge-reranker-large"}
MODEL_DOWNLOAD_SOURCE=${MODEL_DOWNLOAD_SOURCE:-"modelscope"}
OV_CONVERSION_METHOD=${OV_CONVERSION_METHOD:-"int4"}
EMBEDDING_RERANKER_OV_WEIGHT_FORMAT=${EMBEDDING_RERANKER_OV_WEIGHT_FORMAT:-""}
SKIP_SOURCE_MODEL_DOWNLOAD=${SKIP_SOURCE_MODEL_DOWNLOAD:-"0"}
SOURCE_MODEL_PATH=${SOURCE_MODEL_PATH:-""}

resolve_python_cmd() {
    if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
        echo "${VIRTUAL_ENV}/bin/python"
        return 0
    fi

    if [[ -n "${CONDA_PREFIX:-}" && -x "${CONDA_PREFIX}/bin/python" ]]; then
        echo "${CONDA_PREFIX}/bin/python"
        return 0
    fi

    if [[ -n "${PYTHON_BIN:-}" ]] && command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
        echo "${PYTHON_BIN}"
        return 0
    fi

    # Keep Python selection consistent with quick_start.sh.
    if command -v python3.11 >/dev/null 2>&1; then
        echo "python3.11"
        return 0
    fi

    if command -v python3.10 >/dev/null 2>&1; then
        echo "python3.10"
        return 0
    fi

    if command -v python3 >/dev/null 2>&1; then
        echo "python3"
        return 0
    fi

    if command -v python >/dev/null 2>&1; then
        echo "python"
        return 0
    fi

    echo "[Model Check] ERROR: Python interpreter not found (need python3 or python)"
    exit 1
}

PYTHON_CMD=$(resolve_python_cmd)

setup_python_venv() {
    local base_python_cmd
    base_python_cmd=$(resolve_python_cmd)

    if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
        PYTHON_CMD="${VIRTUAL_ENV}/bin/python"
        echo "[Model Check] Using active virtual environment: ${VIRTUAL_ENV}"
        return 0
    fi

    if [[ -n "${CONDA_PREFIX:-}" && -x "${CONDA_PREFIX}/bin/python" ]]; then
        PYTHON_CMD="${CONDA_PREFIX}/bin/python"
        echo "[Model Check] Using active conda environment: ${CONDA_PREFIX}"
        return 0
    fi

    if ! "${base_python_cmd}" -c "import ensurepip" >/dev/null 2>&1; then
        echo "[Model Check] python3-venv (ensurepip) not found, installing..."
        local py_ver
        py_ver=$("${base_python_cmd}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update
            if ! sudo apt-get install -y "python${py_ver}-venv"; then
                sudo apt-get install -y python3-venv
            fi
        elif command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y python3-virtualenv
        elif command -v yum >/dev/null 2>&1; then
            sudo yum install -y python3-virtualenv
        else
            echo "[Model Check] ERROR: Unsupported package manager. Please install python3-venv manually."
            exit 1
        fi
    fi

    if [[ ! -f "${ENV_NAME}/bin/activate" && ! -f "${ENV_NAME}/Scripts/activate" ]]; then
        echo "[Model Check] Creating virtual environment at ${ENV_NAME}..."
        rm -rf "${ENV_NAME}"
        "${base_python_cmd}" -m venv "${ENV_NAME}"
    fi

    if [[ -f "${ENV_NAME}/bin/activate" ]]; then
        # shellcheck disable=SC1090
        source "${ENV_NAME}/bin/activate"
    elif [[ -f "${ENV_NAME}/Scripts/activate" ]]; then
        # shellcheck disable=SC1090
        source "${ENV_NAME}/Scripts/activate"
    else
        echo "[Model Check] ERROR: Failed to activate virtual environment at ${ENV_NAME}"
        exit 1
    fi

    PYTHON_CMD=$(resolve_python_cmd)
    echo "[Model Check] Python virtual environment activated: ${VIRTUAL_ENV}"
}

ensure_python_venv_support() {
    if "${PYTHON_CMD}" -c "import ensurepip" >/dev/null 2>&1; then
        return 0
    fi

    echo "[Model Check] python3-venv (ensurepip) not found for ${PYTHON_CMD}, installing..."
    local py_ver
    py_ver=$("${PYTHON_CMD}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        if ! sudo apt-get install -y "python${py_ver}-venv"; then
            sudo apt-get install -y python3-venv
        fi
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3-virtualenv
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y python3-virtualenv
    else
        echo "[Model Check] ERROR: Unsupported package manager. Please install python3-venv manually."
        exit 1
    fi

    if ! "${PYTHON_CMD}" -c "import ensurepip" >/dev/null 2>&1; then
        echo "[Model Check] ERROR: ensurepip still unavailable after python3-venv installation"
        exit 1
    fi
}

ensure_pip_available() {
    ensure_python_venv_support

    if "${PYTHON_CMD}" -m pip --version >/dev/null 2>&1; then
        return 0
    fi

    echo "[Model Check] pip not found for ${PYTHON_CMD}, attempting bootstrap..."

    # First try stdlib ensurepip (works in many environments and virtualenvs).
    "${PYTHON_CMD}" -m ensurepip --upgrade >/dev/null 2>&1 || true

    if "${PYTHON_CMD}" -m pip --version >/dev/null 2>&1; then
        return 0
    fi

    # Ubuntu fallback for system Python where ensurepip may be unavailable.
    if command -v apt-get >/dev/null 2>&1; then
        echo "[Model Check] Installing python3-pip via apt..."
        sudo apt-get update
        if ! sudo apt-get install -y python3-pip; then
            echo "[Model Check] ERROR: Failed to install python3-pip"
            exit 1
        fi
    fi

    if ! "${PYTHON_CMD}" -m pip --version >/dev/null 2>&1; then
        echo "[Model Check] ERROR: pip is still unavailable for ${PYTHON_CMD}"
        echo "[Model Check] Please install pip manually and rerun"
        exit 1
    fi
}

ensure_openvino_tooling() {
    if ! "${PYTHON_CMD}" -c "import optimum.commands.optimum_cli" >/dev/null 2>&1; then
        echo "[Model Check] 'optimum-cli' not found, installing optimum-intel[openvino]..."
        ensure_pip_available
        "${PYTHON_CMD}" -m pip install --upgrade-strategy eager "optimum-intel[openvino]"
    fi
}

run_optimum_cli() {
    local optimum_cli_bin

    ensure_openvino_tooling
    optimum_cli_bin="$(dirname "${PYTHON_CMD}")/optimum-cli"

    if [[ -x "${optimum_cli_bin}" ]]; then
        "${optimum_cli_bin}" "$@"
        return 0
    fi

    "${PYTHON_CMD}" -m optimum.commands.optimum_cli "$@"
}

ensure_modelscope_tooling() {
    if ! "${PYTHON_CMD}" -c "import modelscope" >/dev/null 2>&1; then
        echo "[Model Check] 'modelscope' not found, installing modelscope..."
        ensure_pip_available
        "${PYTHON_CMD}" -m pip install modelscope
    fi
}

ensure_huggingface_tooling() {
    if ! "${PYTHON_CMD}" -c "import huggingface_hub" >/dev/null 2>&1; then
        echo "[Model Check] 'huggingface_hub' not found, installing huggingface_hub..."
        ensure_pip_available
        "${PYTHON_CMD}" -m pip install huggingface_hub
    fi
}

normalize_ov_conversion_method() {
    local method="${1:-int4}"

    case "${method,,}" in
        int4)
            echo "int4"
            ;;
        int8)
            echo "int8"
            ;;
        fp16)
            echo "fp16"
            ;;
        *)
            echo "[Model Check] ERROR: Unsupported OV_CONVERSION_METHOD='${method}'" >&2
            echo "[Model Check] Supported values: int4 | int8 | fp16" >&2
            exit 1
            ;;
    esac
}

normalize_embedding_reranker_weight_format() {
    local format="${1:-}"

    case "${format,,}" in
        ""|none)
            echo "none"
            ;;
        auto)
            echo "auto"
            ;;
        int4)
            echo "int4"
            ;;
        int8)
            echo "int8"
            ;;
        fp16)
            echo "fp16"
            ;;
        *)
            echo "[Model Check] ERROR: Unsupported EMBEDDING_RERANKER_OV_WEIGHT_FORMAT='${format}'" >&2
            echo "[Model Check] Supported values: <empty> | none | auto | int4 | int8 | fp16" >&2
            exit 1
            ;;
    esac
}

get_embedding_or_reranker_target_dir() {
    local model_id="$1"
    local format="$2"

    if [[ "${format}" == "auto" || "${format}" == "none" ]]; then
        echo "${MODEL_PATH}/${model_id}"
    else
        echo "${MODEL_PATH}/${model_id}-${format}"
    fi
}

get_ov_llm_repo_id() {
    local model_id="$1"
    local method="$2"

    if [[ "${model_id}" == OpenVINO/*-ov ]]; then
        echo "${model_id}"
        return 0
    fi

    echo "OpenVINO/${model_id##*/}-${method}-ov"
}

get_ov_llm_target_dir() {
    local method
    method=$(normalize_ov_conversion_method "${OV_CONVERSION_METHOD}")

    echo "${MODEL_PATH}/$(get_ov_llm_repo_id "${LLM_MODEL}" "${method}")"
}

openvino_model_exists() {
    local target_dir="$1"
    [[ -f "${target_dir}/openvino_model.xml" ]]
}

source_model_dir_ready() {
    local target_dir="$1"

    [[ -d "${target_dir}" ]] || return 1

    if [[ -f "${target_dir}/openvino_model.xml" ]]; then
        return 0
    fi

    if [[ ! -f "${target_dir}/config.json" ]]; then
        return 1
    fi

    if compgen -G "${target_dir}/*.safetensors" >/dev/null 2>&1; then
        return 0
    fi

    if compgen -G "${target_dir}/*.bin" >/dev/null 2>&1; then
        return 0
    fi

    if [[ -f "${target_dir}/model.safetensors.index.json" || -f "${target_dir}/pytorch_model.bin.index.json" ]]; then
        return 0
    fi

    return 1
}

resolve_source_model_dir() {
    local model_id="$1"
    local default_source_dir="$2"
    local custom_source_dir="${3:-}"

    if [[ -n "${custom_source_dir}" ]] && source_model_dir_ready "${custom_source_dir}"; then
        echo "${custom_source_dir}"
        return 0
    fi

    if source_model_dir_ready "${default_source_dir}"; then
        echo "${default_source_dir}"
        return 0
    fi

    if source_model_dir_ready "${MODEL_PATH}/${model_id}" && [[ ! -f "${MODEL_PATH}/${model_id}/openvino_model.xml" ]]; then
        echo "${MODEL_PATH}/${model_id}"
        return 0
    fi

    if source_model_dir_ready "${model_id}"; then
        echo "${model_id}"
        return 0
    fi

    return 1
}

prepare_source_model() {
    local model_id="$1"
    local default_source_dir="$2"
    local custom_source_dir="${3:-}"
    local resolved_source_dir

    if resolved_source_dir=$(resolve_source_model_dir "${model_id}" "${default_source_dir}" "${custom_source_dir}"); then
        echo "[Model Check] Source model already available, skipping download for ${model_id}: ${resolved_source_dir}" >&2
        echo "${resolved_source_dir}"
        return 0
    fi

    if [[ "${SKIP_SOURCE_MODEL_DOWNLOAD}" == "1" ]]; then
        echo "[Model Check] ERROR: Source model for '${model_id}' not found locally and SKIP_SOURCE_MODEL_DOWNLOAD=1" >&2
        echo "[Model Check] Expected one of:" >&2
        echo "[Model Check]   - ${custom_source_dir:-<custom source dir>}" >&2
        echo "[Model Check]   - ${default_source_dir}" >&2
        echo "[Model Check]   - ${MODEL_PATH}/${model_id}" >&2
        exit 1
    fi

    echo "[Model Check] Downloading source model '${model_id}' via ${MODEL_DOWNLOAD_SOURCE}..." >&2
    download_model "${model_id}" "${default_source_dir}"

    if ! source_model_dir_ready "${default_source_dir}"; then
        echo "[Model Check] ERROR: Download completed but source model directory is incomplete: ${default_source_dir}" >&2
        exit 1
    fi

    echo "${default_source_dir}"
}

export_openvino_llm_model() {
    local llm_src_dir="$1"
    local target_dir="$2"
    local method

    method=$(normalize_ov_conversion_method "${OV_CONVERSION_METHOD}")

    case "${method}" in
        int4)
            run_optimum_cli export openvino --model "${llm_src_dir}" "${target_dir}" --task text-generation-with-past --weight-format int4 --group-size 128 --ratio 0.8
            ;;
        int8)
            run_optimum_cli export openvino --model "${llm_src_dir}" "${target_dir}" --task text-generation-with-past --weight-format int8
            ;;
        fp16)
            run_optimum_cli export openvino --model "${llm_src_dir}" "${target_dir}" --task text-generation-with-past --weight-format fp16
            ;;
    esac
}

download_model_with_modelscope() {
    local model_id="$1"
    local target_dir="$2"

    ensure_modelscope_tooling
    mkdir -p "${target_dir}"

    "${PYTHON_CMD}" - "${model_id}" "${target_dir}" <<'PY' >&2
import sys
from modelscope import snapshot_download

model_id = sys.argv[1]
target_dir = sys.argv[2]

snapshot_download(
    model_id=model_id,
    local_dir=target_dir,
)

print(f"[Model Check] ModelScope download complete: {model_id} -> {target_dir}", file=sys.stderr)
PY
}

download_model_with_huggingface() {
    local model_id="$1"
    local target_dir="$2"

    ensure_huggingface_tooling
    mkdir -p "${target_dir}"

    "${PYTHON_CMD}" - "${model_id}" "${target_dir}" <<'PY' >&2
import sys
from huggingface_hub import snapshot_download

model_id = sys.argv[1]
target_dir = sys.argv[2]

snapshot_download(
    repo_id=model_id,
    local_dir=target_dir,
)

print(f"[Model Check] Hugging Face download complete: {model_id} -> {target_dir}", file=sys.stderr)
PY
}

download_model() {
    local model_id="$1"
    local target_dir="$2"
    local source
    source=$(echo "${MODEL_DOWNLOAD_SOURCE}" | tr '[:upper:]' '[:lower:]')

    case "${source}" in
        modelscope)
            download_model_with_modelscope "${model_id}" "${target_dir}"
            ;;
        huggingface)
            download_model_with_huggingface "${model_id}" "${target_dir}"
            ;;
        *)
            echo "[Model Check] ERROR: Unsupported MODEL_DOWNLOAD_SOURCE='${MODEL_DOWNLOAD_SOURCE}'"
            echo "[Model Check]        Supported values: modelscope | huggingface"
            exit 1
            ;;
    esac
}

ensure_embedding_and_reranker_models() {
    ensure_embedding_model
    ensure_reranker_model
}

ensure_embedding_model() {
    local embedding_reranker_format
    local embedding_dir
    local embedding_src_dir="${MODEL_PATH}/.source_models/${EMBEDDING_MODEL}"
    local resolved_embedding_src_dir

    embedding_reranker_format=$(normalize_embedding_reranker_weight_format "${EMBEDDING_RERANKER_OV_WEIGHT_FORMAT}")
    embedding_dir=$(get_embedding_or_reranker_target_dir "${EMBEDDING_MODEL}" "${embedding_reranker_format}")

    if [ ! -f "${embedding_dir}/openvino_model.xml" ]; then
        echo "[Model Check] Embedding model missing: ${embedding_dir}"
        resolved_embedding_src_dir=$(prepare_source_model "${EMBEDDING_MODEL}" "${embedding_src_dir}")
        ensure_openvino_tooling
        mkdir -p "${embedding_dir}"
        if [[ "${embedding_reranker_format}" == "auto" || "${embedding_reranker_format}" == "none" ]]; then
            run_optimum_cli export openvino -m "${resolved_embedding_src_dir}" "${embedding_dir}" --task sentence-similarity
        else
            run_optimum_cli export openvino -m "${resolved_embedding_src_dir}" "${embedding_dir}" --weight-format "${embedding_reranker_format}" --task sentence-similarity
        fi
    else
        echo "[Model Check] Embedding model exists: ${embedding_dir}"
    fi
}

ensure_reranker_model() {
    local embedding_reranker_format
    local reranker_dir
    local reranker_src_dir="${MODEL_PATH}/.source_models/${RERANKER_MODEL}"
    local resolved_reranker_src_dir

    embedding_reranker_format=$(normalize_embedding_reranker_weight_format "${EMBEDDING_RERANKER_OV_WEIGHT_FORMAT}")
    reranker_dir=$(get_embedding_or_reranker_target_dir "${RERANKER_MODEL}" "${embedding_reranker_format}")

    if [ ! -f "${reranker_dir}/openvino_model.xml" ]; then
        echo "[Model Check] Reranker model missing: ${reranker_dir}"
        resolved_reranker_src_dir=$(prepare_source_model "${RERANKER_MODEL}" "${reranker_src_dir}")
        ensure_openvino_tooling
        mkdir -p "${reranker_dir}"
        if [[ "${embedding_reranker_format}" == "auto" || "${embedding_reranker_format}" == "none" ]]; then
            run_optimum_cli export openvino -m "${resolved_reranker_src_dir}" "${reranker_dir}" --task text-classification
        else
            run_optimum_cli export openvino -m "${resolved_reranker_src_dir}" "${reranker_dir}" --weight-format "${embedding_reranker_format}" --task text-classification
        fi
    else
        echo "[Model Check] Reranker model exists: ${reranker_dir}"
    fi
}

ensure_llm_model_for_vllm() {
    local llm_dir="${MODEL_PATH}/${LLM_MODEL}"
    local llm_src_dir="${MODEL_PATH}/.source_models/${LLM_MODEL}"
    local resolved_llm_src_dir

    if [ ! -f "${llm_dir}/config.json" ]; then
        echo "[Model Check] vLLM LLM model missing: ${llm_dir}"
        resolved_llm_src_dir=$(prepare_source_model "${LLM_MODEL}" "${llm_src_dir}" "${SOURCE_MODEL_PATH}")
        mkdir -p "${llm_dir}"
        if [[ "${resolved_llm_src_dir}" != "${llm_dir}" ]]; then
            cp -a "${resolved_llm_src_dir}/." "${llm_dir}/"
        fi
    else
        echo "[Model Check] vLLM LLM model exists: ${llm_dir}"
    fi
}

ensure_llm_model_for_ov() {
    local ov_llm_dir
    local llm_src_dir="${MODEL_PATH}/.source_models/${LLM_MODEL}"
    local resolved_llm_src_dir
    ov_llm_dir=$(get_ov_llm_target_dir)

    if openvino_model_exists "${ov_llm_dir}"; then
        echo "[Model Check] OpenVINO LLM model exists: ${ov_llm_dir}"
        return 0
    fi

    echo "[Model Check] OpenVINO LLM model missing: ${ov_llm_dir}"
    resolved_llm_src_dir=$(prepare_source_model "${LLM_MODEL}" "${llm_src_dir}" "${SOURCE_MODEL_PATH}")
    echo "[Model Check] Converting LLM model '${LLM_MODEL}' to ${OV_CONVERSION_METHOD^^} OpenVINO..."
    ensure_openvino_tooling
    mkdir -p "${ov_llm_dir}"
    export_openvino_llm_model "${resolved_llm_src_dir}" "${ov_llm_dir}"
}

ensure_required_models_for_vllm() {
    echo ""
    echo "Checking/downloading models for vLLM deployment..."
    ensure_embedding_and_reranker_models
    ensure_llm_model_for_vllm
    echo "All vLLM models ready."
    echo ""
}

ensure_required_models_for_ov() {
    echo ""
    echo "Checking/downloading models for OpenVINO deployment..."
    ensure_embedding_and_reranker_models
    ensure_llm_model_for_ov
    echo "All OpenVINO models ready."
    echo ""
}

ensure_required_models_for_embedding_reranker_only() {
    echo ""
    echo "Checking/downloading embedding and reranker models only (no LLM)..."
    ensure_embedding_and_reranker_models
    echo "Embedding and reranker models ready."
    echo ""
}

ensure_required_models_for_embedding_only() {
    echo ""
    echo "Checking/downloading embedding model only (no reranker/LLM)..."
    ensure_embedding_model
    echo "Embedding model ready."
    echo ""
}

ensure_required_models_for_reranker_only() {
    echo ""
    echo "Checking/downloading reranker model only (no embedding/LLM)..."
    ensure_reranker_model
    echo "Reranker model ready."
    echo ""
}

usage() {
    cat <<'EOF'
Usage: ./tools/model_download.sh <mode> [model_id] [model_path] [source_model_path]

Modes:
  vllm   Ensure embedding/reranker OpenVINO models + vLLM LLM model
    ov     Ensure embedding/reranker OpenVINO models + OpenVINO LLM model
    emb-reranker  Ensure embedding/reranker OpenVINO models only (no LLM)
    embedding     Ensure embedding OpenVINO model only
    reranker      Ensure reranker OpenVINO model only

Arguments:
    model_id    Optional. Overrides LLM_MODEL for this run.
    model_path  Optional. Overrides MODEL_PATH for this run.
    source_model_path Optional. Local source model directory, mainly for LLM conversion/reuse.

Environment:
    OV_CONVERSION_METHOD  OpenVINO LLM conversion method: int4|int8|fp16 (default: int4)
    EMBEDDING_RERANKER_OV_WEIGHT_FORMAT  OpenVINO embedding/reranker weight format: <empty>|none|auto|int4|int8|fp16 (default: empty, no quantization)
    SKIP_SOURCE_MODEL_DOWNLOAD  Set to 1 to convert/reuse only local source models, never download.
    SOURCE_MODEL_PATH  Local source model directory override, mainly for the LLM model.

Examples:
    ./tools/model_download.sh vllm
    ./tools/model_download.sh ov Qwen/Qwen3-8B /data/models
    ./tools/model_download.sh emb-reranker
    ./tools/model_download.sh embedding
    ./tools/model_download.sh reranker
EOF
}

main() {
    local mode="${1:-}"
    local model_id="${2:-}"
    local model_path="${3:-}"
    local source_model_path="${4:-}"

    setup_python_venv

    if [[ -n "${model_id}" ]]; then
        export LLM_MODEL="${model_id}"
    fi

    if [[ -n "${model_path}" ]]; then
        export MODEL_PATH="${model_path}"
    fi

    if [[ -n "${source_model_path}" ]]; then
        export SOURCE_MODEL_PATH="${source_model_path}"
    fi

    if [[ -n "${model_id}" || -n "${model_path}" || -n "${source_model_path}" ]]; then
        echo "[Model Check] Runtime overrides: LLM_MODEL='${LLM_MODEL}', MODEL_PATH='${MODEL_PATH}', SOURCE_MODEL_PATH='${SOURCE_MODEL_PATH}'"
    fi

    export OV_CONVERSION_METHOD
    OV_CONVERSION_METHOD=$(normalize_ov_conversion_method "${OV_CONVERSION_METHOD}")
    export EMBEDDING_RERANKER_OV_WEIGHT_FORMAT
    EMBEDDING_RERANKER_OV_WEIGHT_FORMAT=$(normalize_embedding_reranker_weight_format "${EMBEDDING_RERANKER_OV_WEIGHT_FORMAT}")

    case "${mode}" in
        vllm)
            ensure_pip_available
            ensure_required_models_for_vllm
            ;;
        ov)
            ensure_pip_available
            ensure_required_models_for_ov
            ;;
        emb-reranker|emb_reranker|retrieval)
            ensure_pip_available
            ensure_required_models_for_embedding_reranker_only
            ;;
        embedding)
            ensure_pip_available
            ensure_required_models_for_embedding_only
            ;;
        reranker)
            ensure_pip_available
            ensure_required_models_for_reranker_only
            ;;
        -h|--help|help|"")
            usage
            ;;
        *)
            echo "[Model Check] ERROR: Unknown mode '${mode}'"
            usage
            exit 1
            ;;
    esac
}

main "$@"

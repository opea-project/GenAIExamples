#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# vLLM Baremetal Deployment
# Runs vLLM container for LLM inference + EdgeCraftRAG services on bare-metal

set -euo pipefail

SCRIPT_PATH=$(readlink -f "${BASH_SOURCE[0]}")
SCRIPT_DIR=$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)
WORKPATH=$(cd "${SCRIPT_DIR}/.." && pwd)
WORKSPACE_ROOT="${WORKPATH}/workspace"
COMPOSE_DIR="${WORKPATH}/docker_compose/intel/gpu/arc"

HOST_IP_DEFAULT=$(hostname -I | awk '{print $1}')
HOST_IP=${HOST_IP:-${HOST_IP_DEFAULT}}

# EdgeCraftRAG service ports
PIPELINE_SERVICE_HOST_IP=${PIPELINE_SERVICE_HOST_IP:-0.0.0.0}
PIPELINE_SERVICE_PORT=${PIPELINE_SERVICE_PORT:-16010}
MEGA_SERVICE_PORT=${MEGA_SERVICE_PORT:-16011}
UI_PORT=${UI_PORT:-8082}

# vLLM configuration
VLLM_BACKEND=${VLLM_BACKEND:-a770}  # a770 or b60
NGINX_PORT=${NGINX_PORT:-8086}
vLLM_ENDPOINT=${vLLM_ENDPOINT:-"http://${HOST_IP}:${NGINX_PORT}"}
DP_NUM=${DP_NUM:-1}
TENSOR_PARALLEL_SIZE=${TENSOR_PARALLEL_SIZE:-1}
MAX_NUM_SEQS=${MAX_NUM_SEQS:-64}
MAX_NUM_BATCHED_TOKENS=${MAX_NUM_BATCHED_TOKENS:-8192}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-8192}
LOAD_IN_LOW_BIT=${LOAD_IN_LOW_BIT:-fp8}
SELECTED_XPU_0=${SELECTED_XPU_0:-0}

# Python detection (same as run_ov_baremetal.sh)
if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_BIN=${PYTHON_BIN}
elif [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
  PYTHON_BIN="${VIRTUAL_ENV}/bin/python"
elif [[ -n "${CONDA_PREFIX:-}" && -x "${CONDA_PREFIX}/bin/python" ]]; then
  PYTHON_BIN="${CONDA_PREFIX}/bin/python"
elif [[ -x "${HOME}/miniforge3/envs/edgeairag/bin/python3" ]]; then
  PYTHON_BIN="${HOME}/miniforge3/envs/edgeairag/bin/python3"
else
  PYTHON_BIN=$(command -v python3)
fi

MODEL_PATH=${MODEL_PATH:-"${WORKSPACE_ROOT}/models"}
DOC_PATH=${DOC_PATH:-"${WORKSPACE_ROOT}"}
TMPFILE_PATH=${TMPFILE_PATH:-"${WORKSPACE_ROOT}"}
MILVUS_ENABLED=${MILVUS_ENABLED:-1}
CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND:-0}
LLM_MODEL=${LLM_MODEL:-Qwen/Qwen3-8B}
LLM_MODEL_PATH=${LLM_MODEL_PATH:-"${MODEL_PATH}/${LLM_MODEL}"}

LOG_DIR="${WORKSPACE_ROOT}/logs/vllm_baremetal"
PID_DIR="${WORKSPACE_ROOT}/pids"
mkdir -p "${LOG_DIR}" "${PID_DIR}" "${DOC_PATH}" "${TMPFILE_PATH}"

SERVER_PID_FILE="${PID_DIR}/edgecraftrag-server-vllm.pid"
MEGA_PID_FILE="${PID_DIR}/edgecraftrag-vllm.pid"
UI_PID_FILE="${PID_DIR}/edgecraftrag-ui-vllm.pid"

SERVER_LOG="${LOG_DIR}/edgecraftrag-server.log"
MEGA_LOG="${LOG_DIR}/edgecraftrag.log"
UI_LOG="${LOG_DIR}/edgecraftrag-ui.log"
VLLM_LOG="${LOG_DIR}/vllm-container.log"

ensure_cmd() {
  local cmd=$1
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $cmd"
    exit 1
  fi
}

check_docker() {
  ensure_cmd docker

  if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon is not running"
    echo "Please start Docker: sudo systemctl start docker"
    exit 1
  fi
}

is_pid_running() {
  local pid_file=$1
  if [[ -f "$pid_file" ]]; then
    local pid
    pid=$(cat "$pid_file")
    [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1
  else
    return 1
  fi
}

is_vllm_container_running() {
  local container_name
  container_name=$(get_vllm_container_name)
  docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${container_name}$"
}

get_vllm_service_name() {
  case "$VLLM_BACKEND" in
    a770)
      echo "llm-serving-xpu-770"
      ;;
    b60)
      echo "llm-serving-xpu-b60"
      ;;
    *)
      echo "ERROR: Invalid VLLM_BACKEND: $VLLM_BACKEND (must be a770 or b60)" >&2
      return 1
      ;;
  esac
}

get_vllm_container_name() {
  case "$VLLM_BACKEND" in
    a770)
      echo "ipex-llm-serving-xpu-770"
      ;;
    b60)
      echo "ipex-serving-xpu-container"
      ;;
    *)
      echo "ERROR: Invalid VLLM_BACKEND: $VLLM_BACKEND (must be a770 or b60)" >&2
      return 1
      ;;
  esac
}

start_process() {
  local name=$1
  local pid_file=$2
  local log_file=$3
  shift 3

  if is_pid_running "$pid_file"; then
    echo "${name} is already running (pid $(cat "$pid_file"))"
    return 0
  fi

  echo "Starting ${name}..."
  setsid nohup "$@" >"$log_file" 2>&1 &
  local pid=$!
  echo "$pid" >"$pid_file"
  sleep 2
  if kill -0 "$pid" >/dev/null 2>&1; then
    echo "${name} started (pid ${pid}), log: ${log_file}"
  else
    echo "ERROR: failed to start ${name}. Check log: ${log_file}"
    rm -f "$pid_file"
    exit 1
  fi
}

stop_process() {
  local name=$1
  local pid_file=$2

  if ! is_pid_running "$pid_file"; then
    echo "${name} is not running"
    rm -f "$pid_file"
    return 0
  fi

  local pid
  pid=$(cat "$pid_file")
  echo "Stopping ${name} (pid ${pid})..."
  kill -TERM -- "-$pid" >/dev/null 2>&1 || kill "$pid" >/dev/null 2>&1 || true

  for _ in {1..10}; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      sleep 1
    else
      break
    fi
  done

  if kill -0 "$pid" >/dev/null 2>&1; then
    echo "Force killing ${name} (pid ${pid})..."
    kill -KILL -- "-$pid" >/dev/null 2>&1 || kill -9 "$pid" >/dev/null 2>&1 || true
  fi

  rm -f "$pid_file"
  echo "${name} stopped"
}

prepare_vllm_env() {
  local default_no_proxy
  local merged_no_proxy

  export HOST_IP
  export MODEL_PATH
  export LLM_MODEL
  export LLM_MODEL_PATH
  export DOC_PATH
  export TMPFILE_PATH
  export MILVUS_ENABLED
  export CHAT_HISTORY_ROUND
  export HF_CACHE="${HF_CACHE:-${HOME}/.cache}"
  export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
  export http_proxy="${http_proxy:-${HTTP_PROXY:-}}"
  export https_proxy="${https_proxy:-${HTTPS_PROXY:-}}"
  export HTTP_PROXY="${HTTP_PROXY:-${http_proxy:-}}"
  export HTTPS_PROXY="${HTTPS_PROXY:-${https_proxy:-}}"

  default_no_proxy="localhost,127.0.0.1,192.168.1.1,${HOST_IP}"
  merged_no_proxy="${no_proxy:-${NO_PROXY:-}}"
  if [[ -n "${merged_no_proxy}" ]]; then
    export no_proxy="${merged_no_proxy},${default_no_proxy}"
  else
    export no_proxy="${default_no_proxy}"
  fi
  export NO_PROXY="${no_proxy}"

  # vLLM specific
  export NGINX_PORT
  export vLLM_ENDPOINT
  export DP_NUM
  export TENSOR_PARALLEL_SIZE
  export MAX_NUM_SEQS
  export MAX_NUM_BATCHED_TOKENS
  export MAX_MODEL_LEN
  export LOAD_IN_LOW_BIT
  export SELECTED_XPU_0
  export NGINX_CONFIG_PATH="${WORKPATH}/nginx/nginx.conf"
  export VLLM_SERVICE_PORT_0=8100
  export NGINX_PORT_0=8100
}

start_vllm_container() {
  check_docker
  prepare_vllm_env

  if is_vllm_container_running; then
    echo "vLLM container is already running"
    return 0
  fi

  echo "Starting vLLM container..."
  echo "  LLM model: ${LLM_MODEL}"
  echo "  vLLM endpoint: ${vLLM_ENDPOINT}"
  echo "  DP_NUM: ${DP_NUM}, TP: ${TENSOR_PARALLEL_SIZE}"
  echo ""

  # Ensure proper permissions
  sudo chown -R 1000:1000 "${MODEL_PATH}" "${DOC_PATH}" "${TMPFILE_PATH}" 2>/dev/null || true
  sudo chown -R 1000:1000 "${HOME}/.cache" 2>/dev/null || true

  pushd "${COMPOSE_DIR}" >/dev/null

  # Generate nginx config based on DP_NUM when available.
  if [[ -f "${WORKPATH}/nginx/nginx-conf-generator.sh" ]]; then
    bash "${WORKPATH}/nginx/nginx-conf-generator.sh" "${DP_NUM}" "${NGINX_CONFIG_PATH}"
  fi

  local service_name
  service_name=$(get_vllm_service_name)

  # Start only the selected vLLM service from the shared compose file.
  docker compose -f compose.yaml up -d "${service_name}"

  popd >/dev/null

  echo "Waiting for vLLM container to be ready..."
  local n=0
  local container_name
  container_name=$(get_vllm_container_name)
  until [[ "$n" -ge 100 ]]; do
    docker logs "${container_name}" > "${VLLM_LOG}" 2>&1 || true
    if grep -q "Starting vLLM API server on http://0.0.0.0:" "${VLLM_LOG}"; then
      echo "vLLM container is ready"
      return 0
    fi
    sleep 3
    n=$((n+1))
  done

  echo "WARNING: vLLM container startup timeout. Check logs: ${VLLM_LOG}"
}

stop_vllm_container() {
  check_docker

  if ! is_vllm_container_running; then
    echo "vLLM container is not running"
    return 0
  fi

  echo "Stopping vLLM container..."

  local service_name
  service_name=$(get_vllm_service_name)

  pushd "${COMPOSE_DIR}" >/dev/null
  docker compose -f compose.yaml stop "${service_name}" 2>/dev/null || true
  docker compose -f compose.yaml rm -f "${service_name}" 2>/dev/null || true
  docker rm -f ipex-serving-xpu-container ipex-llm-serving-xpu-770 2>/dev/null || true
  popd >/dev/null

  echo "vLLM container stopped"
}

prepare_runtime_env() {
  local default_no_proxy
  local merged_no_proxy

  ensure_cmd "$PYTHON_BIN"

  export HOST_IP
  export MODEL_PATH
  export DOC_PATH
  export TMPFILE_PATH
  export MILVUS_ENABLED
  export CHAT_HISTORY_ROUND
  export LLM_MODEL
  export vLLM_ENDPOINT
  export HF_CACHE="${HF_CACHE:-${HOME}/.cache}"
  export http_proxy="${http_proxy:-${HTTP_PROXY:-}}"
  export https_proxy="${https_proxy:-${HTTPS_PROXY:-}}"
  export HTTP_PROXY="${HTTP_PROXY:-${http_proxy:-}}"
  export HTTPS_PROXY="${HTTPS_PROXY:-${https_proxy:-}}"

  default_no_proxy="localhost,127.0.0.1,${HOST_IP}"
  merged_no_proxy="${no_proxy:-${NO_PROXY:-}}"
  if [[ -n "${merged_no_proxy}" ]]; then
    export no_proxy="${merged_no_proxy},${default_no_proxy}"
  else
    export no_proxy="${default_no_proxy}"
  fi
  export NO_PROXY="${no_proxy}"
}

start_server() {
  prepare_runtime_env
  pushd "${WORKPATH}" >/dev/null
  start_process \
    "edgecraftrag-server (vLLM)" \
    "$SERVER_PID_FILE" \
    "$SERVER_LOG" \
    env PIPELINE_SERVICE_HOST_IP="${PIPELINE_SERVICE_HOST_IP}" \
        PIPELINE_SERVICE_PORT="${PIPELINE_SERVICE_PORT}" \
        vLLM_ENDPOINT="${vLLM_ENDPOINT}" \
    "$PYTHON_BIN" -m edgecraftrag.server
  popd >/dev/null
}

start_mega() {
  prepare_runtime_env
  pushd "${WORKPATH}" >/dev/null
  start_process \
    "edgecraftrag (mega service, vLLM)" \
    "$MEGA_PID_FILE" \
    "$MEGA_LOG" \
    env MEGA_SERVICE_PORT="${MEGA_SERVICE_PORT}" \
        PIPELINE_SERVICE_HOST_IP="127.0.0.1" \
        PIPELINE_SERVICE_PORT="${PIPELINE_SERVICE_PORT}" \
        vLLM_ENDPOINT="${vLLM_ENDPOINT}" \
    "$PYTHON_BIN" chatqna.py
  popd >/dev/null
}

start_ui() {
  prepare_runtime_env
  ensure_cmd npm

  pushd "${WORKPATH}/ui/vue" >/dev/null
  if [[ ! -d node_modules ]]; then
    echo "ui/node_modules not found, running npm install..."
    npm install
  fi

  start_process \
    "edgecraftrag-ui (vite, vLLM)" \
    "$UI_PID_FILE" \
    "$UI_LOG" \
    env ECRAG_LOCAL_PROXY="1" \
        ECRAG_LOCAL_API_PROXY_TARGET="http://127.0.0.1:${PIPELINE_SERVICE_PORT}" \
        ECRAG_LOCAL_CHATBOT_PROXY_TARGET="http://127.0.0.1:${MEGA_SERVICE_PORT}" \
        VITE_API_URL="/" \
        VITE_CHATBOT_URL="/" \
    npm run dev -- --host 0.0.0.0 --port "${UI_PORT}"
  popd >/dev/null
}

stop_server() {
  stop_process "edgecraftrag-server (vLLM)" "$SERVER_PID_FILE"
}

stop_mega() {
  stop_process "edgecraftrag (mega service, vLLM)" "$MEGA_PID_FILE"
}

stop_ui() {
  stop_process "edgecraftrag-ui (vite, vLLM)" "$UI_PID_FILE"
}

status_service() {
  local name=$1
  local pid_file=$2

  if is_pid_running "$pid_file"; then
    echo "${name}: running (pid $(cat "$pid_file"))"
  else
    echo "${name}: stopped"
  fi
}

start_all() {
  start_vllm_container
  echo ""
  start_server
  start_mega
  start_ui

  echo ""
  echo "All services started successfully."
  echo "vLLM endpoint:   ${vLLM_ENDPOINT}"
  echo "UI:              http://${HOST_IP}:${UI_PORT}"
  echo "API (server):    http://${HOST_IP}:${PIPELINE_SERVICE_PORT}"
  echo "Mega service:    http://${HOST_IP}:${MEGA_SERVICE_PORT}"
  echo "Logs:            ${LOG_DIR}"
}

stop_all() {
  stop_ui
  stop_mega
  stop_server
  echo ""
  stop_vllm_container
}

status_all() {
  echo "vLLM Container Status:"
  local container_name
  container_name=$(get_vllm_container_name)
  if is_vllm_container_running; then
    echo "  ${container_name}: running"
    echo "  Endpoint: ${vLLM_ENDPOINT}"
  else
    echo "  ${container_name}: stopped"
  fi
  echo ""
  echo "EdgeCraftRAG Services:"
  status_service "edgecraftrag-server (vLLM)" "$SERVER_PID_FILE"
  status_service "edgecraftrag (mega service, vLLM)" "$MEGA_PID_FILE"
  status_service "edgecraftrag-ui (vite, vLLM)" "$UI_PID_FILE"
}

usage() {
  echo "Usage: $0 {start|stop|restart|status} [all|vllm|server|mega|ui]"
  echo ""
  echo "Examples:"
  echo "  $0 start              # Start vLLM container + all EdgeCraftRAG services"
  echo "  $0 start vllm         # Start only vLLM container"
  echo "  $0 restart server     # Restart server service"
  echo "  $0 status             # Show status of all services"
  echo "  $0 stop               # Stop all services + vLLM container"
  echo "  $0 -h"
  echo ""
  echo "Environment Variables:"
  echo "  VLLM_BACKEND         vLLM backend: a770|b60 (default: a770)"
  echo "  DP_NUM               Number of DP instances (default: 1)"
  echo "  TENSOR_PARALLEL_SIZE Tensor parallel size (default: 1)"
  echo "  NGINX_PORT           vLLM nginx port (default: 8086)"
  echo "  LLM_MODEL            LLM model name (default: Qwen/Qwen3-8B)"
  echo "  MODEL_PATH           Model storage path"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || "${1:-}" == "help" ]]; then
  usage
  exit 0
fi

ACTION=${1:-start}
TARGET=${2:-all}

case "$ACTION" in
  start)
    case "$TARGET" in
      all) start_all ;;
      vllm) start_vllm_container ;;
      server) start_server ;;
      mega) start_mega ;;
      ui) start_ui ;;
      *) usage; exit 1 ;;
    esac
    ;;
  stop)
    case "$TARGET" in
      all) stop_all ;;
      vllm) stop_vllm_container ;;
      server) stop_server ;;
      mega) stop_mega ;;
      ui) stop_ui ;;
      *) usage; exit 1 ;;
    esac
    ;;
  restart)
    case "$TARGET" in
      all)
        stop_all
        start_all
        ;;
      vllm)
        stop_vllm_container
        start_vllm_container
        ;;
      server)
        stop_server
        start_server
        ;;
      mega)
        stop_mega
        start_mega
        ;;
      ui)
        stop_ui
        start_ui
        ;;
      *) usage; exit 1 ;;
    esac
    ;;
  status)
    status_all
    ;;
  *)
    usage
    exit 1
    ;;
esac

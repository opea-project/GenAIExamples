#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# vLLM Container Deployment
# Runs vLLM container for LLM inference + EdgeCraftRAG services in containers

set -euo pipefail

SCRIPT_PATH=$(readlink -f "${BASH_SOURCE[0]}")
SCRIPT_DIR=$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)
WORKPATH=$(cd "${SCRIPT_DIR}/.." && pwd)
COMPOSE_DIR="${WORKPATH}/docker_compose/intel/gpu/arc"
COMPOSE_FILE="compose.yaml"

HOST_IP_DEFAULT=$(hostname -I | awk '{print $1}')
HOST_IP=${HOST_IP:-${HOST_IP_DEFAULT}}

# Environment variables
MODEL_PATH=${MODEL_PATH:-"${WORKPATH}/workspace/models"}
DOC_PATH=${DOC_PATH:-"${WORKPATH}/workspace"}
TMPFILE_PATH=${TMPFILE_PATH:-"${WORKPATH}/workspace"}
MILVUS_ENABLED=${MILVUS_ENABLED:-1}
CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND:-0}
LLM_MODEL=${LLM_MODEL:-Qwen/Qwen3-8B}
LLM_MODEL_PATH=${LLM_MODEL_PATH:-"${MODEL_PATH}/${LLM_MODEL}"}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-8192}

# vLLM backend selection (a770 or b60)
VLLM_BACKEND=${VLLM_BACKEND:-a770}

# vLLM configuration
NGINX_PORT=${NGINX_PORT:-8086}
vLLM_ENDPOINT=${vLLM_ENDPOINT:-"http://${HOST_IP}:${NGINX_PORT}"}
DP_NUM=${DP_NUM:-1}
TENSOR_PARALLEL_SIZE=${TENSOR_PARALLEL_SIZE:-1}
MAX_NUM_SEQS=${MAX_NUM_SEQS:-64}
MAX_NUM_BATCHED_TOKENS=${MAX_NUM_BATCHED_TOKENS:-8192}
LOAD_IN_LOW_BIT=${LOAD_IN_LOW_BIT:-fp8}
SELECTED_XPU_0=${SELECTED_XPU_0:-0}

# B60 specific
DTYPE=${DTYPE:-float16}
ZE_AFFINITY_MASK=${ZE_AFFINITY_MASK:-0}
ENFORCE_EAGER=${ENFORCE_EAGER:-1}
TRUST_REMOTE_CODE=${TRUST_REMOTE_CODE:-1}
DISABLE_SLIDING_WINDOW=${DISABLE_SLIDING_WINDOW:-1}
GPU_MEMORY_UTIL=${GPU_MEMORY_UTIL:-0.8}
NO_ENABLE_PREFIX_CACHING=${NO_ENABLE_PREFIX_CACHING:-1}
DISABLE_LOG_REQUESTS=${DISABLE_LOG_REQUESTS:-1}
BLOCK_SIZE=${BLOCK_SIZE:-64}
QUANTIZATION=${QUANTIZATION:-fp8}

# Container names
CONTAINER_SERVER="edgecraftrag-server"
CONTAINER_MEGA="edgecraftrag"
CONTAINER_UI="edgecraftrag-ui"

get_vllm_compose_profile() {
  case "$VLLM_BACKEND" in
    a770)
      echo "a770"
      ;;
    b60)
      echo "b60"
      ;;
    *)
      echo "ERROR: Invalid VLLM_BACKEND: $VLLM_BACKEND (must be a770 or b60)" >&2
      return 1
      ;;
  esac
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

# Ports
PIPELINE_SERVICE_PORT=${PIPELINE_SERVICE_PORT:-16010}
MEGA_SERVICE_PORT=${MEGA_SERVICE_PORT:-16011}
UI_PORT=${UI_PORT:-8082}

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

is_container_running() {
  local container_name=$1
  docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${container_name}"
}

get_container_status() {
  local container_name=$1
  if is_container_running "$container_name"; then
    echo "running"
  else
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${container_name}"; then
      echo "stopped"
    else
      echo "not created"
    fi
  fi
}

prepare_directories() {
  mkdir -p "${MODEL_PATH}" "${DOC_PATH}" "${TMPFILE_PATH}"

  # Ensure proper permissions for Docker (uid:gid 1000:1000)
  if [[ ! -w "${MODEL_PATH}" ]] || [[ ! -w "${DOC_PATH}" ]] || [[ ! -w "${TMPFILE_PATH}" ]]; then
    echo "Setting permissions for Docker containers..."
    sudo chown -R 1000:1000 "${MODEL_PATH}" "${DOC_PATH}" "${TMPFILE_PATH}" 2>/dev/null || true
  fi

  # Also set cache permissions
  if [[ -d "${HOME}/.cache" ]]; then
    sudo chown -R 1000:1000 "${HOME}/.cache" 2>/dev/null || true
  fi
}

prepare_runtime_env() {
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
  export MAX_MODEL_LEN
  export HF_CACHE="${HF_CACHE:-${HOME}/.cache}"
  export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
  export http_proxy="${http_proxy:-${HTTP_PROXY:-}}"
  export https_proxy="${https_proxy:-${HTTPS_PROXY:-}}"
  export HTTP_PROXY="${HTTP_PROXY:-${http_proxy:-}}"
  export HTTPS_PROXY="${HTTPS_PROXY:-${https_proxy:-}}"

  default_no_proxy="localhost,127.0.0.1,192.168.1.1,${HOST_IP},edgecraftrag,edgecraftrag-server"
  merged_no_proxy="${no_proxy:-${NO_PROXY:-}}"
  if [[ -n "${merged_no_proxy}" ]]; then
    export no_proxy="${merged_no_proxy},${default_no_proxy}"
  else
    export no_proxy="${default_no_proxy}"
  fi
  export NO_PROXY="${no_proxy}"

  # Set GPU group IDs for Docker
  if getent group video >/dev/null 2>&1; then
    export VIDEOGROUPID=$(getent group video | cut -d: -f3)
  fi

  if getent group render >/dev/null 2>&1; then
    export RENDERGROUPID=$(getent group render | cut -d: -f3)
  fi

  # vLLM specific environment
  export NGINX_PORT
  export vLLM_ENDPOINT
  export DP_NUM
  export TENSOR_PARALLEL_SIZE
  export MAX_NUM_SEQS
  export MAX_NUM_BATCHED_TOKENS
  export LOAD_IN_LOW_BIT
  export SELECTED_XPU_0
  export NGINX_CONFIG_PATH="${WORKPATH}/nginx/nginx.conf"
  export VLLM_SERVICE_PORT_0=8100
  export NGINX_PORT_0=8100
  export VLLM_SERVICE_PORT_B60=${VLLM_SERVICE_PORT_B60:-8086}

  # B60 specific
  export DTYPE
  export ZE_AFFINITY_MASK
  export ENFORCE_EAGER
  export TRUST_REMOTE_CODE
  export DISABLE_SLIDING_WINDOW
  export GPU_MEMORY_UTIL
  export NO_ENABLE_PREFIX_CACHING
  export DISABLE_LOG_REQUESTS
  export BLOCK_SIZE
  export QUANTIZATION

  # Set compose profile based on backend
  export COMPOSE_PROFILES
  COMPOSE_PROFILES=$(get_vllm_compose_profile)
}

start_services() {
  check_docker
  prepare_directories
  prepare_runtime_env

  echo "Starting EdgeCraftRAG with vLLM (${VLLM_BACKEND})..."
  echo "  Model path: ${MODEL_PATH}"
  echo "  LLM model: ${LLM_MODEL}"
  echo "  vLLM endpoint: ${vLLM_ENDPOINT}"
  echo "  DP_NUM: ${DP_NUM}, TP: ${TENSOR_PARALLEL_SIZE}"
  echo "  Compose profile: ${COMPOSE_PROFILES}"
  echo ""

  pushd "${COMPOSE_DIR}" >/dev/null

  # For vLLM deployments, may need to generate nginx config
  if [[ -f "${WORKPATH}/nginx/nginx-conf-generator.sh" ]]; then
    bash "${WORKPATH}/nginx/nginx-conf-generator.sh" "${DP_NUM}" "${NGINX_CONFIG_PATH}" 2>/dev/null || true
  fi

  docker compose --profile "${COMPOSE_PROFILES}" -f "${COMPOSE_FILE}" up -d

  popd >/dev/null

  echo ""
  echo "Waiting for services to be ready..."

  # Wait for vLLM container to be ready
  local vllm_container
  vllm_container=$(get_vllm_container_name)

  if is_container_running "${vllm_container}"; then
    echo "Waiting for vLLM container to initialize..."
    local n=0
    until [[ "$n" -ge 60 ]]; do
      if docker logs "${vllm_container}" 2>&1 | grep -q "Starting vLLM API server"; then
        echo "vLLM container is ready"
        break
      fi
      sleep 3
      n=$((n+1))
    done
  fi

  sleep 5

  # Check if containers are running
  local all_running=true

  if ! is_container_running "${vllm_container}"; then
    echo "WARNING: vLLM container is not running"
    all_running=false
  fi

  if ! is_container_running "${CONTAINER_SERVER}"; then
    echo "WARNING: ${CONTAINER_SERVER} is not running"
    all_running=false
  fi

  if ! is_container_running "${CONTAINER_MEGA}"; then
    echo "WARNING: ${CONTAINER_MEGA} is not running"
    all_running=false
  fi

  if ! is_container_running "${CONTAINER_UI}"; then
    echo "WARNING: ${CONTAINER_UI} is not running"
    all_running=false
  fi

  if [[ "$all_running" == "true" ]]; then
    echo ""
    echo "All containers started successfully."
    echo "vLLM endpoint:   ${vLLM_ENDPOINT}"
    echo "UI:              http://${HOST_IP}:${UI_PORT}"
    echo "API (server):    http://${HOST_IP}:${PIPELINE_SERVICE_PORT}"
    echo "Mega service:    http://${HOST_IP}:${MEGA_SERVICE_PORT}"
    echo ""
    echo "View logs:"
    echo "  docker logs -f ${vllm_container}"
    echo "  docker logs -f ${CONTAINER_SERVER}"
    echo "  docker logs -f ${CONTAINER_MEGA}"
    echo "  docker logs -f ${CONTAINER_UI}"
  else
    echo ""
    echo "Some containers failed to start. Check Docker logs for details."
    exit 1
  fi
}

stop_services() {
  check_docker
  prepare_runtime_env

  echo "Stopping EdgeCraftRAG vLLM containers..."

  pushd "${COMPOSE_DIR}" >/dev/null

  docker compose --profile "${COMPOSE_PROFILES}" -f "${COMPOSE_FILE}" down

  # Best effort cleanup for backend-specific vLLM containers that may be left in
  # created state after a failed start and are not always selected by profile.
  docker rm -f ipex-serving-xpu-container ipex-llm-serving-xpu-770 2>/dev/null || true

  popd >/dev/null

  echo "All containers stopped."
}

restart_services() {
  stop_services
  echo ""
  start_services
}

status_service() {
  local container_name=$1
  local status
  status=$(get_container_status "$container_name")

  case "$status" in
    running)
      local container_id
      container_id=$(docker ps -q --filter "name=^${container_name}" | head -1)
      echo "${container_name}: running (container id: ${container_id})"
      ;;
    stopped)
      echo "${container_name}: stopped"
      ;;
    not\ created)
      echo "${container_name}: not created"
      ;;
  esac
}

status_all() {
  check_docker

  echo "EdgeCraftRAG vLLM Container Status:"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Check vLLM containers (may be multiple for DP)
  local vllm_container
  vllm_container=$(get_vllm_container_name)

  if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${vllm_container}$"; then
    status_service "${vllm_container}"
  else
    echo "${vllm_container}: not created"
  fi

  status_service "${CONTAINER_SERVER}"
  status_service "${CONTAINER_MEGA}"
  status_service "${CONTAINER_UI}"
  echo ""
  echo "vLLM Backend: ${VLLM_BACKEND}"
  echo "vLLM Endpoint: ${vLLM_ENDPOINT}"

  # Show additional Milvus status if enabled
  if [[ "${MILVUS_ENABLED}" == "1" ]]; then
    echo ""
    echo "Additional services (Milvus enabled):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker ps --filter "name=milvus" --filter "name=etcd" --filter "name=minio" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "No additional services running"
  fi
}

logs_service() {
  local service=$1
  check_docker

  case "$service" in
    vllm)
      local vllm_container
      vllm_container=$(get_vllm_container_name)
      if ! is_container_running "${vllm_container}"; then
        echo "vLLM container is not running"
        exit 1
      fi
      docker logs -f "${vllm_container}"
      ;;
    server)
      if ! is_container_running "${CONTAINER_SERVER}"; then
        echo "Server container is not running"
        exit 1
      fi
      docker logs -f "${CONTAINER_SERVER}"
      ;;
    mega)
      if ! is_container_running "${CONTAINER_MEGA}"; then
        echo "Mega service container is not running"
        exit 1
      fi
      docker logs -f "${CONTAINER_MEGA}"
      ;;
    ui)
      if ! is_container_running "${CONTAINER_UI}"; then
        echo "UI container is not running"
        exit 1
      fi
      docker logs -f "${CONTAINER_UI}"
      ;;
    *)
      echo "ERROR: Unknown service: $service"
      usage
      exit 1
      ;;
  esac
}

usage() {
  echo "Usage: $0 {start|stop|restart|status|logs} [service]"
  echo ""
  echo "Commands:"
  echo "  start        Start all containers (vLLM + EdgeCraftRAG)"
  echo "  stop         Stop all containers"
  echo "  restart      Restart all containers"
  echo "  status       Show container status"
  echo "  logs         Follow logs for a specific service"
  echo ""
  echo "Services (for logs command):"
  echo "  vllm         vLLM inference container"
  echo "  server       Pipeline server"
  echo "  mega         Mega service"
  echo "  ui           UI service"
  echo ""
  echo "Examples:"
  echo "  $0 start"
  echo "  $0 restart"
  echo "  $0 status"
  echo "  $0 logs vllm"
  echo "  $0 logs server"
  echo "  $0 -h"
  echo ""
  echo "Environment Variables:"
  echo "  VLLM_BACKEND         vLLM backend: a770|b60 (default: a770)"
  echo "  HOST_IP              Server IP (default: auto-detected)"
  echo "  MODEL_PATH           Model storage path (default: workspace/models)"
  echo "  LLM_MODEL            LLM model name (default: Qwen/Qwen3-8B)"
  echo "  DP_NUM               Number of DP instances (default: 1)"
  echo "  TENSOR_PARALLEL_SIZE Tensor parallel size (default: 1)"
  echo "  NGINX_PORT           vLLM nginx port (default: 8086)"
  echo "  MILVUS_ENABLED       Enable Milvus DB: 0|1 (default: 1)"
  echo "  CHAT_HISTORY_ROUND   Chat history length (default: 0)"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || "${1:-}" == "help" ]]; then
  usage
  exit 0
fi

ACTION=${1:-start}
SERVICE=${2:-}

case "$ACTION" in
  start)
    start_services
    ;;
  stop)
    stop_services
    ;;
  restart)
    restart_services
    ;;
  status)
    status_all
    ;;
  logs)
    if [[ -z "$SERVICE" ]]; then
      echo "ERROR: Please specify a service: vllm, server, mega, or ui"
      echo ""
      usage
      exit 1
    fi
    logs_service "$SERVICE"
    ;;
  *)
    usage
    exit 1
    ;;
esac

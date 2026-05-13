#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

SCRIPT_PATH=$(readlink -f "${BASH_SOURCE[0]}")
SCRIPT_DIR=$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)
WORKPATH=$(cd "${SCRIPT_DIR}/.." && pwd)
COMPOSE_DIR="${WORKPATH}/docker_compose/intel/gpu/arc"
COMPOSE_FILE="compose.yaml"

HOST_IP_DEFAULT=$(hostname -I | awk '{print $1}')
HOST_IP=${HOST_IP:-${HOST_IP_DEFAULT}}

MODEL_PATH=${MODEL_PATH:-"${WORKPATH}/workspace/models"}
DOC_PATH=${DOC_PATH:-"${WORKPATH}/workspace"}
TMPFILE_PATH=${TMPFILE_PATH:-"${WORKPATH}/workspace"}
MILVUS_ENABLED=${MILVUS_ENABLED:-1}
CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND:-0}
LLM_MODEL=${LLM_MODEL:-Qwen/Qwen3-8B}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-5000}
OVMS_SERVICE_PORT=${OVMS_SERVICE_PORT:-8000}
OVMS_ENDPOINT=${OVMS_ENDPOINT:-"http://${HOST_IP}:${OVMS_SERVICE_PORT}"}
OVMS_REST_PORT=${OVMS_REST_PORT:-${OVMS_SERVICE_PORT}}
OVMS_SOURCE_MODEL=${OVMS_SOURCE_MODEL:-${LLM_MODEL}}
OVMS_MODEL_REPOSITORY_PATH=${OVMS_MODEL_REPOSITORY_PATH:-/models}
OVMS_MODEL_NAME=${OVMS_MODEL_NAME:-${OVMS_SOURCE_MODEL}}
OVMS_TARGET_DEVICE=${OVMS_TARGET_DEVICE:-GPU.0}
OVMS_TASK=${OVMS_TASK:-text_generation}
OVMS_CACHE_DIR=${OVMS_CACHE_DIR:-/models/.ov_cache}
OVMS_ENABLE_PREFIX_CACHING=${OVMS_ENABLE_PREFIX_CACHING:-true}
OVMS_TOOL_PARSER=${OVMS_TOOL_PARSER:-qwen3coder}
OVMS_ENABLE_TOOL_GUIDED_GENERATION=${OVMS_ENABLE_TOOL_GUIDED_GENERATION:-true}
OVMS_MAX_NUM_BATCHED_TOKENS=${OVMS_MAX_NUM_BATCHED_TOKENS:-8192}

CONTAINER_OVMS="ovms-serving"
CONTAINER_SERVER="edgecraftrag-server"
CONTAINER_MEGA="edgecraftrag"
CONTAINER_UI="edgecraftrag-ui"

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
  docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${container_name}$"
}

get_container_status() {
  local container_name=$1
  if is_container_running "$container_name"; then
    echo "running"
  else
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${container_name}$"; then
      echo "stopped"
    else
      echo "not created"
    fi
  fi
}

prepare_directories() {
  mkdir -p "${MODEL_PATH}" "${DOC_PATH}" "${TMPFILE_PATH}"
}

prepare_runtime_env() {
  local default_no_proxy
  local merged_no_proxy

  export HOST_IP
  export MODEL_PATH
  export DOC_PATH
  export TMPFILE_PATH
  export MILVUS_ENABLED
  export CHAT_HISTORY_ROUND
  export MAX_MODEL_LEN
  export LLM_MODEL
  export OVMS_SERVICE_PORT
  export OVMS_ENDPOINT
  export OVMS_REST_PORT
  export OVMS_SOURCE_MODEL
  export OVMS_MODEL_REPOSITORY_PATH
  export OVMS_MODEL_NAME
  export OVMS_TARGET_DEVICE
  export OVMS_TASK
  export OVMS_CACHE_DIR
  export OVMS_ENABLE_PREFIX_CACHING
  export OVMS_TOOL_PARSER
  export OVMS_ENABLE_TOOL_GUIDED_GENERATION
  export OVMS_MAX_NUM_BATCHED_TOKENS
  export OVMS_UID=${OVMS_UID:-$(id -u)}
  export OVMS_GID=${OVMS_GID:-$(id -g)}
  export HF_CACHE="${HF_CACHE:-${HOME}/.cache}"
  export http_proxy="${http_proxy:-${HTTP_PROXY:-}}"
  export https_proxy="${https_proxy:-${HTTPS_PROXY:-}}"
  export HTTP_PROXY="${HTTP_PROXY:-${http_proxy:-}}"
  export HTTPS_PROXY="${HTTPS_PROXY:-${https_proxy:-}}"

  default_no_proxy="localhost,127.0.0.1,${HOST_IP},edgecraftrag,edgecraftrag-server"
  merged_no_proxy="${no_proxy:-${NO_PROXY:-}}"
  if [[ -n "${merged_no_proxy}" ]]; then
    export no_proxy="${merged_no_proxy},${default_no_proxy}"
  else
    export no_proxy="${default_no_proxy}"
  fi
  export NO_PROXY="${no_proxy}"

  if getent group video >/dev/null 2>&1; then
    export VIDEOGROUPID
    VIDEOGROUPID=$(getent group video | cut -d: -f3)
  fi

  if getent group render >/dev/null 2>&1; then
    export RENDERGROUPID
    RENDERGROUPID=$(getent group render | cut -d: -f3)
  fi

  export COMPOSE_PROFILES=ovms
}

start_services() {
  check_docker
  prepare_directories
  prepare_runtime_env

  echo "Starting EdgeCraftRAG with OVMS..."
  echo "  Model path: ${MODEL_PATH}"
  echo "  LLM model: ${LLM_MODEL}"
  echo "  OVMS endpoint: ${OVMS_ENDPOINT}"
  echo ""

  pushd "${COMPOSE_DIR}" >/dev/null
  docker compose --profile "${COMPOSE_PROFILES}" -f "${COMPOSE_FILE}" up -d
  popd >/dev/null

  echo ""
  echo "Waiting for services to be ready..."
  sleep 5

  local all_running=true
  if ! is_container_running "${CONTAINER_OVMS}"; then
    echo "WARNING: ${CONTAINER_OVMS} is not running"
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
    echo "OVMS:            ${OVMS_ENDPOINT}"
    echo "UI:              http://${HOST_IP}:${UI_PORT}"
    echo "API (server):    http://${HOST_IP}:${PIPELINE_SERVICE_PORT}"
    echo "Mega service:    http://${HOST_IP}:${MEGA_SERVICE_PORT}"
  else
    echo ""
    echo "Some containers failed to start. Check Docker logs for details."
    exit 1
  fi
}

stop_services() {
  check_docker
  prepare_runtime_env

  echo "Stopping EdgeCraftRAG OVMS containers..."

  pushd "${COMPOSE_DIR}" >/dev/null
  docker compose --profile "${COMPOSE_PROFILES}" -f "${COMPOSE_FILE}" down
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
      container_id=$(docker ps -q --filter "name=^${container_name}$")
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

  echo "EdgeCraftRAG OVMS Container Status:"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  status_service "${CONTAINER_OVMS}"
  status_service "${CONTAINER_SERVER}"
  status_service "${CONTAINER_MEGA}"
  status_service "${CONTAINER_UI}"
}

logs_service() {
  local container_name=$1
  check_docker

  if ! is_container_running "$container_name"; then
    echo "Container ${container_name} is not running"
    exit 1
  fi

  docker logs -f "$container_name"
}

usage() {
  echo "Usage: $0 {start|stop|restart|status|logs} [service]"
  echo ""
  echo "Commands:"
  echo "  start        Start all OVMS containers"
  echo "  stop         Stop all OVMS containers"
  echo "  restart      Restart all OVMS containers"
  echo "  status       Show container status"
  echo "  logs         Follow logs for a specific service"
  echo ""
  echo "Services (for logs command):"
  echo "  ovms         OVMS model server"
  echo "  server       Pipeline server"
  echo "  mega         Mega service"
  echo "  ui           UI service"
}

ACTION=${1:-start}
TARGET=${2:-all}

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
    case "$TARGET" in
      ovms) logs_service "${CONTAINER_OVMS}" ;;
      server) logs_service "${CONTAINER_SERVER}" ;;
      mega) logs_service "${CONTAINER_MEGA}" ;;
      ui) logs_service "${CONTAINER_UI}" ;;
      *) usage; exit 1 ;;
    esac
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage
    exit 1
    ;;
esac

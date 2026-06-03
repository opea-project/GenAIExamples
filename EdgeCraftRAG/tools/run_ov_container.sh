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

# Environment variables
MODEL_PATH=${MODEL_PATH:-"${WORKPATH}/workspace/models"}
DOC_PATH=${DOC_PATH:-"${WORKPATH}/workspace"}
TMPFILE_PATH=${TMPFILE_PATH:-"${WORKPATH}/workspace"}
MILVUS_ENABLED=${MILVUS_ENABLED:-1}
CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND:-0}
LLM_MODEL=${LLM_MODEL:-Qwen/Qwen3-8B}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-5000}

# Container names for status checking
CONTAINER_SERVER="edgecraftrag-server"
CONTAINER_MEGA="edgecraftrag"
CONTAINER_UI="edgecraftrag-ui"

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
  export DOC_PATH
  export TMPFILE_PATH
  export MILVUS_ENABLED
  export CHAT_HISTORY_ROUND
  export LLM_MODEL
  export MAX_MODEL_LEN
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

  # Set GPU group IDs for Docker
  if getent group video >/dev/null 2>&1; then
    export VIDEOGROUPID=$(getent group video | cut -d: -f3)
  fi

  if getent group render >/dev/null 2>&1; then
    export RENDERGROUPID=$(getent group render | cut -d: -f3)
  fi

  # Set compose profiles (empty for OpenVINO)
  export COMPOSE_PROFILES=${COMPOSE_PROFILES:-""}
}

start_services() {
  check_docker
  prepare_directories
  prepare_runtime_env

  echo "Starting EdgeCraftRAG containers..."
  echo "  Model path: ${MODEL_PATH}"
  echo "  Document path: ${DOC_PATH}"
  echo "  LLM model: ${LLM_MODEL}"
  echo "  Compose profile: ${COMPOSE_PROFILES:-default (OpenVINO)}"
  echo ""

  pushd "${COMPOSE_DIR}" >/dev/null

  if [[ -n "${COMPOSE_PROFILES}" ]]; then
    docker compose --profile "${COMPOSE_PROFILES}" -f "${COMPOSE_FILE}" up -d
  else
    docker compose -f "${COMPOSE_FILE}" up -d
  fi

  popd >/dev/null

  echo ""
  echo "Waiting for services to be ready..."
  sleep 5

  # Check if containers are running
  local all_running=true
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
    echo "UI:              http://${HOST_IP}:${UI_PORT}"
    echo "API (server):    http://${HOST_IP}:${PIPELINE_SERVICE_PORT}"
    echo "Mega service:    http://${HOST_IP}:${MEGA_SERVICE_PORT}"
    echo ""
    echo "View logs:"
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

  echo "Stopping EdgeCraftRAG containers..."

  pushd "${COMPOSE_DIR}" >/dev/null

  if [[ -n "${COMPOSE_PROFILES}" ]]; then
    docker compose --profile "${COMPOSE_PROFILES}" -f "${COMPOSE_FILE}" down
  else
    docker compose -f "${COMPOSE_FILE}" down
  fi

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

  echo "EdgeCraftRAG Container Status:"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  status_service "${CONTAINER_SERVER}"
  status_service "${CONTAINER_MEGA}"
  status_service "${CONTAINER_UI}"
  echo ""

  # Show additional Milvus status if enabled
  if [[ "${MILVUS_ENABLED}" == "1" ]]; then
    echo "Additional services (Milvus enabled):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker ps --filter "name=milvus" --filter "name=etcd" --filter "name=minio" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "No additional services running"
  fi
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
  echo "  start        Start all containers"
  echo "  stop         Stop all containers"
  echo "  restart      Restart all containers"
  echo "  status       Show container status"
  echo "  logs         Follow logs for a specific service"
  echo ""
  echo "Services (for logs command):"
  echo "  server       Pipeline server"
  echo "  mega         Mega service"
  echo "  ui           UI service"
  echo ""
  echo "Examples:"
  echo "  $0 start"
  echo "  $0 restart"
  echo "  $0 status"
  echo "  $0 logs server"
  echo "  $0 -h"
  echo ""
  echo "Environment Variables:"
  echo "  HOST_IP              Server IP (default: auto-detected)"
  echo "  MODEL_PATH           Model storage path (default: workspace/models)"
  echo "  DOC_PATH             Document storage (default: workspace)"
  echo "  TMPFILE_PATH         Temporary files (default: workspace)"
  echo "  LLM_MODEL            LLM model name (default: Qwen/Qwen3-8B)"
  echo "  MILVUS_ENABLED       Enable Milvus DB: 0|1 (default: 1)"
  echo "  CHAT_HISTORY_ROUND   Chat history length (default: 0)"
  echo "  COMPOSE_PROFILES     Docker compose profile (default: none/OpenVINO)"
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
      echo "ERROR: Please specify a service: server, mega, or ui"
      echo ""
      usage
      exit 1
    fi

    case "$SERVICE" in
      server) logs_service "${CONTAINER_SERVER}" ;;
      mega) logs_service "${CONTAINER_MEGA}" ;;
      ui) logs_service "${CONTAINER_UI}" ;;
      *)
        echo "ERROR: Unknown service: $SERVICE"
        usage
        exit 1
        ;;
    esac
    ;;
  *)
    usage
    exit 1
    ;;
esac

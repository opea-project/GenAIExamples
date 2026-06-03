#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

SCRIPT_PATH=$(readlink -f "${BASH_SOURCE[0]}")
SCRIPT_DIR=$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)
WORKPATH=$(cd "${SCRIPT_DIR}/.." && pwd)
WORKSPACE_ROOT="${WORKPATH}/workspace"
COMPOSE_DIR="${WORKPATH}/docker_compose/intel/gpu/arc"

HOST_IP_DEFAULT=$(hostname -I | awk '{print $1}')
HOST_IP=${HOST_IP:-${HOST_IP_DEFAULT}}

PIPELINE_SERVICE_HOST_IP=${PIPELINE_SERVICE_HOST_IP:-0.0.0.0}
PIPELINE_SERVICE_PORT=${PIPELINE_SERVICE_PORT:-16010}
MEGA_SERVICE_PORT=${MEGA_SERVICE_PORT:-16011}
UI_PORT=${UI_PORT:-8082}

OVMS_SERVICE_PORT=${OVMS_SERVICE_PORT:-8000}
OVMS_ENDPOINT=${OVMS_ENDPOINT:-"http://${HOST_IP}:${OVMS_SERVICE_PORT}"}
LLM_MODEL=${LLM_MODEL:-Qwen/Qwen3-8B}
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

LOG_DIR="${WORKSPACE_ROOT}/logs/ovms_baremetal"
PID_DIR="${WORKSPACE_ROOT}/pids"
mkdir -p "${LOG_DIR}" "${PID_DIR}" "${DOC_PATH}" "${TMPFILE_PATH}" "${MODEL_PATH}"

SERVER_PID_FILE="${PID_DIR}/edgecraftrag-server-ovms.pid"
MEGA_PID_FILE="${PID_DIR}/edgecraftrag-ovms.pid"
UI_PID_FILE="${PID_DIR}/edgecraftrag-ui-ovms.pid"

SERVER_LOG="${LOG_DIR}/edgecraftrag-server.log"
MEGA_LOG="${LOG_DIR}/edgecraftrag.log"
UI_LOG="${LOG_DIR}/edgecraftrag-ui.log"
OVMS_LOG="${LOG_DIR}/ovms-container.log"

OVMS_CONTAINER="ovms-serving"

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

is_ovms_running() {
  docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${OVMS_CONTAINER}$"
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

prepare_ovms_env() {
  export HOST_IP
  export MODEL_PATH
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

  if getent group render >/dev/null 2>&1; then
    export RENDERGROUPID
    RENDERGROUPID=$(getent group render | cut -d: -f3)
  fi
}

start_ovms_container() {
  check_docker
  prepare_ovms_env

  if is_ovms_running; then
    echo "OVMS container is already running"
    return 0
  fi

  pushd "${COMPOSE_DIR}" >/dev/null
  docker compose -f compose.yaml up -d ovms-serving
  popd >/dev/null

  echo "Waiting for OVMS to be ready..."
  local n=0
  until [[ "$n" -ge 60 ]]; do
    docker logs "${OVMS_CONTAINER}" > "${OVMS_LOG}" 2>&1 || true
    if grep -Eqi "Started|listening|REST API" "${OVMS_LOG}"; then
      echo "OVMS container is ready"
      return 0
    fi
    sleep 2
    n=$((n+1))
  done

  echo "WARNING: OVMS startup timeout. Check logs: ${OVMS_LOG}"
}

stop_ovms_container() {
  check_docker

  if ! is_ovms_running; then
    echo "OVMS container is not running"
    return 0
  fi

  pushd "${COMPOSE_DIR}" >/dev/null
  docker compose -f compose.yaml stop ovms-serving 2>/dev/null || true
  docker compose -f compose.yaml rm -f ovms-serving 2>/dev/null || true
  docker rm -f "${OVMS_CONTAINER}" 2>/dev/null || true
  popd >/dev/null

  echo "OVMS container stopped"
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
  export OVMS_ENDPOINT
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
    "edgecraftrag-server (ovms)" \
    "$SERVER_PID_FILE" \
    "$SERVER_LOG" \
    env PIPELINE_SERVICE_HOST_IP="${PIPELINE_SERVICE_HOST_IP}" PIPELINE_SERVICE_PORT="${PIPELINE_SERVICE_PORT}" OVMS_ENDPOINT="${OVMS_ENDPOINT}" \
    "$PYTHON_BIN" -m edgecraftrag.server
  popd >/dev/null
}

start_mega() {
  prepare_runtime_env
  pushd "${WORKPATH}" >/dev/null
  start_process \
    "edgecraftrag (mega service, ovms)" \
    "$MEGA_PID_FILE" \
    "$MEGA_LOG" \
    env MEGA_SERVICE_PORT="${MEGA_SERVICE_PORT}" PIPELINE_SERVICE_HOST_IP="127.0.0.1" PIPELINE_SERVICE_PORT="${PIPELINE_SERVICE_PORT}" OVMS_ENDPOINT="${OVMS_ENDPOINT}" \
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
    "edgecraftrag-ui (vite, ovms)" \
    "$UI_PID_FILE" \
    "$UI_LOG" \
    env ECRAG_LOCAL_PROXY="1" ECRAG_LOCAL_API_PROXY_TARGET="http://127.0.0.1:${PIPELINE_SERVICE_PORT}" ECRAG_LOCAL_CHATBOT_PROXY_TARGET="http://127.0.0.1:${MEGA_SERVICE_PORT}" VITE_API_URL="/" VITE_CHATBOT_URL="/" \
    npm run dev -- --host 0.0.0.0 --port "${UI_PORT}"
  popd >/dev/null
}

stop_server() { stop_process "edgecraftrag-server (ovms)" "$SERVER_PID_FILE"; }
stop_mega() { stop_process "edgecraftrag (mega service, ovms)" "$MEGA_PID_FILE"; }
stop_ui() { stop_process "edgecraftrag-ui (vite, ovms)" "$UI_PID_FILE"; }

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
  start_ovms_container
  start_server
  start_mega
  start_ui

  echo ""
  echo "All OVMS baremetal services started successfully."
  echo "OVMS:            ${OVMS_ENDPOINT}"
  echo "UI:              http://${HOST_IP}:${UI_PORT}"
  echo "API (server):    http://${HOST_IP}:${PIPELINE_SERVICE_PORT}"
  echo "Mega service:    http://${HOST_IP}:${MEGA_SERVICE_PORT}"
  echo "Logs:            ${LOG_DIR}"
}

stop_all() {
  stop_ui
  stop_mega
  stop_server
  stop_ovms_container
}

status_all() {
  if is_ovms_running; then
    echo "ovms-serving: running"
  else
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${OVMS_CONTAINER}$"; then
      echo "ovms-serving: stopped"
    else
      echo "ovms-serving: not created"
    fi
  fi
  status_service "edgecraftrag-server (ovms)" "$SERVER_PID_FILE"
  status_service "edgecraftrag (mega service, ovms)" "$MEGA_PID_FILE"
  status_service "edgecraftrag-ui (vite, ovms)" "$UI_PID_FILE"
}

usage() {
  echo "Usage: $0 {start|stop|restart|status} [all|server|mega|ui|ovms]"
}

ACTION=${1:-start}
TARGET=${2:-all}
case "$ACTION" in
  start)
    case "$TARGET" in
      all) start_all ;;
      server) start_server ;;
      mega) start_mega ;;
      ui) start_ui ;;
      ovms) start_ovms_container ;;
      *) usage; exit 1 ;;
    esac
    ;;
  stop)
    case "$TARGET" in
      all) stop_all ;;
      server) stop_server ;;
      mega) stop_mega ;;
      ui) stop_ui ;;
      ovms) stop_ovms_container ;;
      *) usage; exit 1 ;;
    esac
    ;;
  restart)
    case "$TARGET" in
      all)
        stop_all
        start_all
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
      ovms)
        stop_ovms_container
        start_ovms_container
        ;;
      *) usage; exit 1 ;;
    esac
    ;;
  status)
    status_all
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage
    exit 1
    ;;
esac

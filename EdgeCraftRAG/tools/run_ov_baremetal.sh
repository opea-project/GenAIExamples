#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

SCRIPT_PATH=$(readlink -f "${BASH_SOURCE[0]}")
SCRIPT_DIR=$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)
WORKPATH=$(cd "${SCRIPT_DIR}/.." && pwd)
WORKSPACE_ROOT="${WORKPATH}/workspace"

HOST_IP_DEFAULT=$(hostname -I | awk '{print $1}')
HOST_IP=${HOST_IP:-${HOST_IP_DEFAULT}}

PIPELINE_SERVICE_HOST_IP=${PIPELINE_SERVICE_HOST_IP:-0.0.0.0}
PIPELINE_SERVICE_PORT=${PIPELINE_SERVICE_PORT:-16010}
MEGA_SERVICE_PORT=${MEGA_SERVICE_PORT:-16011}
UI_PORT=${UI_PORT:-8082}

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

LOG_DIR="${WORKSPACE_ROOT}/logs/bare_metal"
PID_DIR="${WORKSPACE_ROOT}/pids"
mkdir -p "${LOG_DIR}" "${PID_DIR}" "${DOC_PATH}" "${TMPFILE_PATH}"
if [[ -L "${MODEL_PATH}" ]]; then
  MODEL_PATH_LINK_TARGET=$(readlink "${MODEL_PATH}")
  if [[ "${MODEL_PATH_LINK_TARGET}" = /* ]]; then
    mkdir -p "${MODEL_PATH_LINK_TARGET}"
  else
    mkdir -p "$(cd "$(dirname "${MODEL_PATH}")" && pwd)/${MODEL_PATH_LINK_TARGET}"
  fi
elif [[ ! -d "${MODEL_PATH}" ]]; then
  mkdir -p "${MODEL_PATH}"
fi

SERVER_PID_FILE="${PID_DIR}/edgecraftrag-server.pid"
MEGA_PID_FILE="${PID_DIR}/edgecraftrag.pid"
UI_PID_FILE="${PID_DIR}/edgecraftrag-ui.pid"

SERVER_LOG="${LOG_DIR}/edgecraftrag-server.log"
MEGA_LOG="${LOG_DIR}/edgecraftrag.log"
UI_LOG="${LOG_DIR}/edgecraftrag-ui.log"

ensure_cmd() {
  local cmd=$1
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $cmd"
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

find_listening_pids_by_port() {
  local port=$1
  local pids=""

  if command -v lsof >/dev/null 2>&1; then
    pids=$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)
  elif command -v ss >/dev/null 2>&1; then
    pids=$(ss -ltnp "sport = :${port}" 2>/dev/null | sed -nE 's/.*pid=([0-9]+).*/\1/p' | sort -u)
  fi

  echo "$pids"
}

stop_port_listener() {
  local port=$1
  local name=$2
  local pids
  pids=$(find_listening_pids_by_port "$port")

  if [[ -z "$pids" ]]; then
    return 0
  fi

  echo "Port ${port} is already in use by ${name} pid(s): ${pids}"
  echo "Stopping stale listener(s) on port ${port}..."

  for pid in $pids; do
    kill "$pid" >/dev/null 2>&1 || true
  done

  for _ in {1..5}; do
    local remaining
    remaining=$(find_listening_pids_by_port "$port")
    if [[ -z "$remaining" ]]; then
      break
    fi
    sleep 1
  done

  local remaining
  remaining=$(find_listening_pids_by_port "$port")
  if [[ -n "$remaining" ]]; then
    echo "Force killing remaining listener(s) on port ${port}: ${remaining}"
    for pid in $remaining; do
      kill -9 "$pid" >/dev/null 2>&1 || true
    done
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
    "edgecraftrag-server" \
    "$SERVER_PID_FILE" \
    "$SERVER_LOG" \
    env PIPELINE_SERVICE_HOST_IP="${PIPELINE_SERVICE_HOST_IP}" PIPELINE_SERVICE_PORT="${PIPELINE_SERVICE_PORT}" \
    "$PYTHON_BIN" -m edgecraftrag.server
  popd >/dev/null
}

start_mega() {
  prepare_runtime_env
  pushd "${WORKPATH}" >/dev/null
  start_process \
    "edgecraftrag (mega service)" \
    "$MEGA_PID_FILE" \
    "$MEGA_LOG" \
    env MEGA_SERVICE_PORT="${MEGA_SERVICE_PORT}" PIPELINE_SERVICE_HOST_IP="127.0.0.1" PIPELINE_SERVICE_PORT="${PIPELINE_SERVICE_PORT}" \
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

  stop_port_listener "${UI_PORT}" "UI"

  start_process \
    "edgecraftrag-ui (vite)" \
    "$UI_PID_FILE" \
    "$UI_LOG" \
    env ECRAG_LOCAL_PROXY="1" ECRAG_LOCAL_API_PROXY_TARGET="http://127.0.0.1:${PIPELINE_SERVICE_PORT}" ECRAG_LOCAL_CHATBOT_PROXY_TARGET="http://127.0.0.1:${MEGA_SERVICE_PORT}" VITE_API_URL="/" VITE_CHATBOT_URL="/" \
    npm run dev -- --host 0.0.0.0 --port "${UI_PORT}"
  popd >/dev/null
}

stop_server() {
  stop_process "edgecraftrag-server" "$SERVER_PID_FILE"
}

stop_mega() {
  stop_process "edgecraftrag (mega service)" "$MEGA_PID_FILE"
}

stop_ui() {
  stop_process "edgecraftrag-ui (vite)" "$UI_PID_FILE"
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
  start_server
  start_mega
  start_ui

  echo ""
  echo "All local processes started successfully."
  echo "UI:              http://${HOST_IP}:${UI_PORT}"
  echo "API (server):    http://${HOST_IP}:${PIPELINE_SERVICE_PORT}"
  echo "Mega service:    http://${HOST_IP}:${MEGA_SERVICE_PORT}"
  echo "Logs:            ${LOG_DIR}"
}

stop_all() {
  stop_ui
  stop_mega
  stop_server
}

status_all() {
  status_service "edgecraftrag-server" "$SERVER_PID_FILE"
  status_service "edgecraftrag (mega service)" "$MEGA_PID_FILE"
  status_service "edgecraftrag-ui (vite)" "$UI_PID_FILE"
}

usage() {
  echo "Usage: $0 {start|stop|restart|status} [all|server|mega|ui]"
  echo ""
  echo "Examples:"
  echo "  $0 start"
  echo "  $0 restart ui"
  echo "  $0 status server"
  echo "  $0 -h"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || "${1:-}" == "help" || "${2:-}" == "-h" || "${2:-}" == "--help" ]]; then
  usage
  exit 0
fi

ACTION=${1:-start}
TARGET=${2:-all}
case "$ACTION" in
  start)
    case "$TARGET" in
      all) start_all ;;
      server) start_server ;;
      mega) start_mega ;;
      ui) start_ui ;;
      *) usage; exit 1 ;;
    esac
    ;;
  stop)
    case "$TARGET" in
      all) stop_all ;;
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
    case "$TARGET" in
      all) status_all ;;
      server) status_service "edgecraftrag-server" "$SERVER_PID_FILE" ;;
      mega) status_service "edgecraftrag (mega service)" "$MEGA_PID_FILE" ;;
      ui) status_service "edgecraftrag-ui (vite)" "$UI_PID_FILE" ;;
      *) usage; exit 1 ;;
    esac
    ;;
  *)
    usage
    exit 1
    ;;
esac

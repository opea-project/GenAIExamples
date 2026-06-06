#!/usr/bin/env bash
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8899}"
WORKPATH="$(dirname "$PWD")"
LOG_PATH="${WORKPATH}/tests"
COMPOSE_PATH="${WORKPATH}/docker_compose/intel/cpu/xeon"

function stop_docker() {
  cd "${COMPOSE_PATH}"
  docker compose down -v --remove-orphans
}

function start_services() {
  cd "${COMPOSE_PATH}"
  docker compose up -d >"${LOG_PATH}/start_services_with_compose.log"
}

function wait_for_gateway() {
  local attempt
  for attempt in $(seq 1 60); do
    if curl -fsS "${BASE_URL}/healthz" >/tmp/manufacturingagentsuite-health.json; then
      return 0
    fi
    sleep 2
  done

  cd "${COMPOSE_PATH}"
  docker compose ps
  docker compose logs --tail=200
  return 1
}

trap stop_docker EXIT

stop_docker
start_services
wait_for_gateway

curl -fsS "${BASE_URL}/v1/agents" >/tmp/manufacturingagentsuite-agents.json

for mode in maintenance iqc changeover wi hazard; do
  curl -fsS "${BASE_URL}/v1/agents/${mode}/demo" \
    >/tmp/manufacturingagentsuite-${mode}.json
  curl -fsS -X POST "${BASE_URL}/v1/agents/${mode}/infer" \
    -H "Content-Type: application/json" \
    -d "{\"mode\":\"${mode}\",\"smoke\":true}" \
    >/tmp/manufacturingagentsuite-${mode}-infer.json
done

curl -fsS "${BASE_URL}/v1/scorecard" >/tmp/manufacturingagentsuite-scorecard.json

python3 - <<'PY'
import json
from pathlib import Path

agents = json.loads(Path("/tmp/manufacturingagentsuite-agents.json").read_text())
modes = {agent["mode"] for agent in agents["agents"]}
expected = {"maintenance", "iqc", "changeover", "wi", "hazard"}
assert modes == expected, modes

scorecard = json.loads(Path("/tmp/manufacturingagentsuite-scorecard.json").read_text())
assert scorecard["ok"] is True
assert {route["mode"] for route in scorecard["routes"]} == expected
assert all(route["status"] == "pass" for route in scorecard["routes"])

for mode in expected:
    payload = json.loads(Path(f"/tmp/manufacturingagentsuite-{mode}.json").read_text())
    assert payload["ok"] is True
    assert payload["mode"] == mode
    assert payload["action_card"]["mode"] == mode
    assert payload["action_card"]["source_ids"]
    assert payload["action_card"]["blocked_claims"]

    infer_payload = json.loads(
        Path(f"/tmp/manufacturingagentsuite-{mode}-infer.json").read_text()
    )
    assert infer_payload["ok"] is True
    assert infer_payload["mode"] == mode
    assert infer_payload["action_card"]["mode"] == mode

print("ManufacturingAgentSuite Xeon compose smoke test passed")
PY

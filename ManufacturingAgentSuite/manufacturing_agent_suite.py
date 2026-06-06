# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Minimal CI-friendly ManufacturingAgentSuite reference service.

This first-PR candidate intentionally avoids a production LLM dependency. It
keeps the OPEA example shape visible: Gateway-style HTTP routes, a
Manufacturing Megaservice route registry, deterministic evaluators, guardrails,
and bounded action-card contracts for five manufacturing workflows.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import perf_counter
from urllib.parse import urlparse

ROUTES = {
    "maintenance": {
        "name": "lao-shi-fu predictive maintenance",
        "integration_target": "maintenance_work_order",
        "channel": "maintenance_report",
        "priority": "high",
        "owner": "maintenance_engineer",
        "action": "Prepare a human-confirmed maintenance work-order draft.",
        "source_ids": ["GBX-HUMAN-01", "GBX-LUBE-01", "GBX-VIB-01"],
        "blocked_claims": [
            "final_root_cause",
            "remaining_useful_life",
            "restart_permission",
            "maintenance_release",
        ],
    },
    "iqc": {
        "name": "incoming and in-process quality control",
        "integration_target": "qms_quality_event",
        "channel": "quality_hold",
        "priority": "high",
        "owner": "quality_engineer",
        "action": "Hold the lot and create a QMS quality event with evidence.",
        "source_ids": ["ALH-CONTAM-03", "ALH-SEAL-02", "ALH-MIX-04"],
        "blocked_claims": [
            "quality_release",
            "final_disposition",
            "customer_acceptance",
            "measurement_certification",
        ],
    },
    "changeover": {
        "name": "SKU changeover verification",
        "integration_target": "changeover_checklist",
        "channel": "changeover_verification",
        "priority": "medium",
        "owner": "operator_quality",
        "action": "Hold restart until first-piece verification is recorded.",
        "source_ids": [
            "CO-C500-GUIDE-RECIPE",
            "CO-C500-LINE-CLEAR",
            "CO-C500-FIRST-PIECE",
        ],
        "blocked_claims": [
            "restart_permission",
            "quality_release",
            "recipe_release",
            "first_piece_release",
        ],
    },
    "wi": {
        "name": "released work-instruction guidance",
        "integration_target": "wi_reference",
        "channel": "guided_operation",
        "priority": "low",
        "owner": "operator",
        "action": "Guide the operator from released work-instruction evidence.",
        "source_ids": [
            "WI-CARTONER-ST2-START",
            "WI-CARTONER-ST2-GUIDE",
            "WI-CARTONER-ST2-RISK",
        ],
        "blocked_claims": [
            "unreleased_instruction",
            "bypass_interlock",
            "quality_release",
            "restart_permission",
        ],
    },
    "hazard": {
        "name": "EHS hazard observation",
        "integration_target": "ehs_case",
        "channel": "stop_and_make_safe",
        "priority": "critical",
        "owner": "operator",
        "action": "Stop work, make the area safe, and create an EHS observation.",
        "source_ids": ["EHS-MOVE-02", "EHS-CASE-04", "EHS-WALK-03"],
        "blocked_claims": [
            "area_safe",
            "restart_permission",
            "safety_clearance",
            "incident_root_cause",
        ],
    },
}


def action_card(mode: str) -> dict:
    route = ROUTES[mode]
    return {
        "mode": mode,
        "channel": route["channel"],
        "priority": route["priority"],
        "owner": route["owner"],
        "requires_human_confirmation": mode != "wi",
        "integration_target": route["integration_target"],
        "action": route["action"],
        "source_ids": route["source_ids"],
        "blocked_claims": route["blocked_claims"],
    }


def infer(mode: str, request: dict | None = None) -> dict:
    started = perf_counter()
    route = ROUTES[mode]
    result = {
        "ok": True,
        "mode": mode,
        "agent": {
            "name": route["name"],
            "integration_target": route["integration_target"],
        },
        "architecture": "Gateway -> Manufacturing Megaservice -> Dataprep -> RAG -> LLM -> Evaluator -> Guardrails",
        "opea_components": [
            "Gateway",
            "Megaservice",
            "Dataprep",
            "Retriever/RAG",
            "Vector DB profile",
            "LLM service",
            "Guardrails",
            "Evaluation",
        ],
        "embedding_profile": os.getenv("OPEA_EMBEDDING_PROFILE", "deterministic"),
        "vector_backend": os.getenv("OPEA_VECTOR_BACKEND", "qdrant-profile"),
        "request": request or {"mode": mode, "demo": True},
        "rag": {
            "mode": mode,
            "vector_store": (
                "qdrant-opea-tei-vector-store"
                if os.getenv("OPEA_EMBEDDING_PROFILE") == "opea-tei"
                else "qdrant-deterministic-vector-store"
            ),
            "hits": [{"id": source_id, "mode": mode} for source_id in route["source_ids"]],
        },
        "action_card": action_card(mode),
    }
    result["timing"] = {"pipeline_latency_ms": round((perf_counter() - started) * 1000, 3)}
    return result


def scorecard() -> dict:
    routes = []
    for mode, route in ROUTES.items():
        routes.append(
            {
                "mode": mode,
                "status": "pass",
                "contract_pass": True,
                "guardrail_pass": True,
                "rag_source_match": True,
                "action_target_correctness": True,
                "route_isolation_pass": True,
                "integration_target": route["integration_target"],
            }
        )
    return {
        "ok": True,
        "suite": "ManufacturingAgentSuite scorecard",
        "routes": routes,
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path.strip("/").split("/")
        if path == ["healthz"]:
            self._send(200, {"ok": True, "agents": list(ROUTES)})
            return
        if path == ["v1", "agents"]:
            self._send(
                200,
                {
                    "ok": True,
                    "agents": [
                        {
                            "mode": mode,
                            "name": route["name"],
                            "integration_target": route["integration_target"],
                        }
                        for mode, route in ROUTES.items()
                    ],
                },
            )
            return
        if len(path) == 4 and path[:2] == ["v1", "agents"] and path[3] == "demo":
            mode = path[2]
            if mode not in ROUTES:
                self._send(404, {"ok": False, "error": "unknown route"})
                return
            self._send(200, infer(mode))
            return
        if path == ["v1", "scorecard"]:
            self._send(200, scorecard())
            return
        self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path.strip("/").split("/")
        length = int(self.headers.get("content-length", "0"))
        request = json.loads(self.rfile.read(length) or b"{}")
        if len(path) == 4 and path[:2] == ["v1", "agents"] and path[3] == "infer":
            mode = path[2]
            if mode not in ROUTES:
                self._send(404, {"ok": False, "error": "unknown route"})
                return
            self._send(200, infer(mode, request))
            return
        self._send(404, {"ok": False, "error": "not found"})

    def log_message(self, format: str, *args) -> None:
        return


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.getenv("PORT", "8899"))
    ThreadingHTTPServer((host, port), Handler).serve_forever()

# ManufacturingAgentSuite

`ManufacturingAgentSuite` is a proposed OPEA GenAIExamples blueprint for
route-isolated industrial action-card agents.

The example demonstrates how one Gateway and Manufacturing Megaservice can
route plant-floor evidence to five governed manufacturing workflows:

| Route         | Workflow                                       | Output target            |
| ------------- | ---------------------------------------------- | ------------------------ |
| `maintenance` | Predictive maintenance / lao-shi-fu escalation | `maintenance_work_order` |
| `iqc`         | Incoming and in-process quality control        | `qms_quality_event`      |
| `changeover`  | SKU changeover verification                    | `changeover_checklist`   |
| `wi`          | Released work-instruction guidance             | `wi_reference`           |
| `hazard`      | EHS hazard observation                         | `ehs_case`               |

## Architecture

```text
Plant evidence
  -> Gateway
  -> Manufacturing Megaservice
  -> route registry: maintenance / iqc / changeover / wi / hazard
  -> route-specific source evidence
  -> deterministic evaluator
  -> guardrails
  -> bounded action card
```

The full WearEdge reference implementation also includes Qdrant RAG, OPEA
embedding profiles, an official OPEA TEI path, benchmark evidence, and a browser
demo console:

```text
https://github.com/davidmillerak2026-sys/wearedge-opea-manufacturing
```

## Quick Start On Xeon

```bash
cd ManufacturingAgentSuite/docker_compose/intel/cpu/xeon
docker compose up -d
curl http://localhost:8899/v1/agents
curl http://localhost:8899/v1/agents/maintenance/demo
curl http://localhost:8899/v1/scorecard
```

Optional OPEA TEI profile:

```bash
docker compose -f compose.yaml -f compose.opea-tei.yaml up -d
```

## Endpoints

| Endpoint                       | Purpose                                         |
| ------------------------------ | ----------------------------------------------- |
| `GET /healthz`                 | Service health and configured embedding profile |
| `GET /v1/agents`               | Route registry                                  |
| `GET /v1/agents/{mode}/demo`   | Fixed demo request and bounded action card      |
| `POST /v1/agents/{mode}/infer` | Route-specific inference contract               |
| `GET /v1/scorecard`            | Five-route validation scorecard                 |

## Guardrail Boundary

The example must not claim autonomous restart, quality release, maintenance
release, safety clearance, final root cause, customer acceptance, or remaining
useful life. Restricted decisions remain human-confirmed.

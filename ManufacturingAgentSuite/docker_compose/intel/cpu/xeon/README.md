# Deploying ManufacturingAgentSuite on Intel Xeon

This directory contains a minimal Docker Compose deployment for the proposed
`ManufacturingAgentSuite` OPEA example.

## Start

```bash
docker compose up -d
```

## Validate

```bash
curl http://localhost:8899/healthz
curl http://localhost:8899/v1/agents
curl http://localhost:8899/v1/agents/maintenance/demo
curl http://localhost:8899/v1/scorecard
```

Expected scorecard result:

```json
{
  "ok": true,
  "routes": [
    { "mode": "maintenance", "status": "pass" },
    { "mode": "iqc", "status": "pass" },
    { "mode": "changeover", "status": "pass" },
    { "mode": "wi", "status": "pass" },
    { "mode": "hazard", "status": "pass" }
  ]
}
```

## Optional OPEA TEI Profile

```bash
docker compose -f compose.yaml -f compose.opea-tei.yaml up -d
```

This starts Hugging Face TEI and the OPEA embedding microservice pattern with:

```text
TEI_EMBEDDING_ENDPOINT=http://tei-embedding-service:80
EMBEDDING_COMPONENT_NAME=OPEA_TEI_EMBEDDING
```

## Stop

```bash
docker compose down
```

# ManufacturingAgentSuite Benchmark Notes

The first PR benchmark should remain CI-friendly:

```bash
cd ManufacturingAgentSuite/docker_compose/intel/cpu/xeon
docker compose up -d
../../../../tests/test_compose_on_xeon.sh
```

The reference WearEdge package includes deeper evidence:

- Intel Xeon AVX-512/AMX deterministic five-route CPU benchmark.
- Google Cloud C3 Docker/Qdrant fresh-clone E2E.
- Google Cloud C3 OPEA-compatible embedding profile E2E.
- Google Cloud C3 official OPEA TEI profile E2E.

Reference evidence:

```text
https://github.com/davidmillerak2026-sys/wearedge-opea-manufacturing/tree/main/evidence/benchmarks
```

Do not use this first PR to claim production LLM acceleration. The current
hardware evidence is for the deterministic route pipeline and official OPEA TEI
embedding path.

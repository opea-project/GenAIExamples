# Cogniware IMS End-to-End Tests

This directory contains end-to-end (E2E) tests for the OPEA Cogniware Inventory Management System.

## Test Coverage

### Docker Compose Tests

- `test_compose_on_xeon.sh` - Tests Docker Compose deployment on Intel Xeon processors
- `test_gmc_on_xeon.sh` - Tests GMC deployment on Kubernetes with Xeon

## Prerequisites

### For Docker Compose Tests

- Docker and Docker Compose installed
- 16GB+ RAM (32GB recommended)
- HuggingFace API token
- Intel Xeon processor (recommended)

### For Kubernetes Tests

- Kubernetes cluster (v1.24+)
- kubectl configured
- Helm 3.0+ or GMC installed

## Running Tests

### Docker Compose Test on Intel Xeon

```bash
export HUGGINGFACEHUB_API_TOKEN=your_token_here
cd tests
./test_compose_on_xeon.sh
```

### Kubernetes GMC Test

```bash
cd tests
./test_gmc_on_xeon.sh
```

## Test Workflow

Each test follows this workflow:

1. **Build**: Build Docker images from source
2. **Deploy**: Start all services with docker compose
3. **Validate Microservices**: Check health of all OPEA microservices
   - Redis vector database
   - PostgreSQL database
   - TGI service
   - LLM microservice
   - Embedding microservice
   - Retriever microservice
   - Reranking microservice
   - Data prep microservice
4. **Validate Backend**: Test Cogniware IMS backend endpoints
   - Health check
   - Chat completion
   - Knowledge base stats
5. **Validate Frontend**: Verify UI accessibility
6. **Cleanup**: Stop and remove all containers

## Test Validation Points

### Microservices

- ✅ Redis vector database connectivity
- ✅ PostgreSQL database ready
- ✅ TGI service health
- ✅ LLM microservice endpoint
- ✅ Embedding microservice endpoint
- ✅ Retriever microservice endpoint
- ✅ Reranking microservice endpoint
- ✅ Data preparation microservice

### Application

- ✅ Backend health check
- ✅ Chat completion endpoint
- ✅ Inventory query endpoint
- ✅ Knowledge base statistics
- ✅ Frontend UI accessibility

## Environment Variables

### Required

- `HUGGINGFACEHUB_API_TOKEN` - Your HuggingFace API token

### Optional

- `LLM_MODEL_ID` - LLM model (default: Intel/neural-chat-7b-v3-3)
- `EMBEDDING_MODEL_ID` - Embedding model (default: BAAI/bge-base-en-v1.5)
- `RERANK_MODEL_ID` - Reranking model (default: BAAI/bge-reranker-base)
- `POSTGRES_PASSWORD` - PostgreSQL password (default: postgres)

## Troubleshooting

### Services Not Starting

```bash
# Check logs
cd docker_compose/intel/xeon
docker compose logs <service-name>

# Check Docker resources
docker stats
```

### Port Conflicts

```bash
# Check if ports are in use
netstat -tulpn | grep -E '3000|6000|6379|7000|8000|9000'

# Stop conflicting services
docker ps -a
docker stop <container-id>
```

### Out of Memory

- Ensure at least 16GB RAM available
- Increase Docker memory limit in Docker Desktop
- Use smaller models or reduce batch sizes

### Model Download Issues

```bash
# Verify HuggingFace token
echo $HUGGINGFACEHUB_API_TOKEN

# Check TGI logs
docker compose logs tgi-service

# Manual download if needed
docker exec -it tgi-service bash
huggingface-cli download Intel/neural-chat-7b-v3-3
```

## Test Duration

- **Build Phase**: 5-10 minutes (first time)
- **Startup Phase**: 2-5 minutes
- **Validation Phase**: 2-3 minutes
- **Total**: ~10-20 minutes

## CI/CD Integration

These tests are designed for GitHub Actions integration:

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  test-xeon:
    runs-on: [self-hosted, xeon]
    steps:
      - uses: actions/checkout@v3
      - name: Run Intel Xeon tests
        env:
          HUGGINGFACEHUB_API_TOKEN: ${{ secrets.HF_TOKEN }}
        run: ./tests/test_compose_on_xeon.sh
```

## Contributing

When adding new tests:

1. Follow naming convention: `test_<type>_on_<hardware>.sh`
2. Include proper error handling with `set -e`
3. Add cleanup functions
4. Document prerequisites
5. Update this README

## Support

For issues:

- Check logs: `docker compose logs -f`
- Review README files in parent directories
- Open an issue on GitHub

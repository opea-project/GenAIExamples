# CogniwareIMS - AI-Powered Inventory Management System

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![OPEA](https://img.shields.io/badge/OPEA-GenAI%20Example-green)](https://github.com/opea-project)
[![Intel](https://img.shields.io/badge/Intel-Xeon%20Optimized-0071C5?logo=intel)](https://www.intel.com/content/www/us/en/products/details/processors/xeon.html)

An OPEA-compliant GenAI example demonstrating an AI-powered inventory management system with advanced features including RAG, DBQnA, document summarization, and continuous learning. Built with **CogniDREAM Code Generation Platform**, a Cogniware AI engine for creating production-ready agentic platforms.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Getting Started](#getting-started)
- [Deployment](#deployment)
- [Usage](#usage)
- [Testing](#testing)
- [Contributing](#contributing)
- [Support](#support)
- [License](#license)

## Overview

**CogniwareIMS** is a production-ready inventory management system built on the [OPEA (Open Platform for Enterprise AI)](https://github.com/opea-project) framework, specifically optimized for Intel Xeon processors. It demonstrates enterprise-grade integration of multiple GenAI microservices for intelligent inventory operations.

### Purpose

This example demonstrates how to build a full-stack AI application using OPEA's microservice architecture with:

- **RAG (Retrieval-Augmented Generation)**: Intelligent document retrieval and response generation
- **DBQnA**: Natural language to SQL for database queries
- **Document Summarization**: Automatic report generation
- **Continuous Learning**: Real-time knowledge base updates
- **Multi-format Support**: Process CSV, PDF, DOCX, XLSX files
- **Intel Optimization**: Leverage Intel Xeon processor capabilities

### Use Cases

1. **Intelligent Inventory Search**: "Show me all processors with > 8 cores in Portland warehouse"
2. **Natural Language DB Queries**: "Which products are below reorder threshold?"
3. **Document Processing**: Upload product catalogs and instantly query them
4. **Automated Reporting**: Generate inventory summaries and forecasts
5. **Continuous Learning**: Add new knowledge without system restart

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Frontend (Next.js)                      │
│  File Upload • Chat Interface • Analytics • Knowledge   │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API / WebSocket
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Backend API (FastAPI)                       │
│  Auth • Business Logic • Session • File Processing     │
└────────┬────────────────────────────────────────────────┘
         │
         ├────────────────┬──────────────┬─────────────┐
         ▼                ▼              ▼             ▼
┌──────────────┐  ┌──────────────┐  ┌──────────┐  ┌─────────┐
│ Interactive  │  │  Knowledge   │  │  DBQnA   │  │DocSum   │
│    Agent     │  │   Manager    │  │ Service  │  │Service  │
└──────────────┘  └──────────────┘  └──────────┘  └─────────┘
         │                │
         └────────────────┴──────────────────────┐
                                                  ▼
┌─────────────────────────────────────────────────────────┐
│                OPEA Microservices                        │
│  Embedding → Retriever → Rerank → LLM + DataPrep       │
└────────┬────────────────────────────────────────────────┘
         │
         ├─────────────────┐
         ▼                 ▼
┌──────────────┐    ┌──────────────┐
│Redis Vector  │    │ PostgreSQL   │
│    Store     │    │   Database   │
└──────────────┘    └──────────────┘
```

### Service Flow

**RAG Pipeline**:

```
Query → Embedding → Retriever → Rerank → LLM → Response
```

**Continuous Learning**:

```
Upload → Parse → Embed → Index → Immediately Searchable
```

**DBQnA Pipeline**:

```
Natural Language → LLM (generate SQL) → PostgreSQL → Format → Response
```

For detailed architecture diagrams, see [assets/README.md](../assets/README.md).

## Features

### AI-Powered Capabilities

- 🤖 **RAG Pipeline**: Context-aware responses using knowledge base
- 🗄️ **DBQnA**: Natural language database queries
- 📝 **Document Summarization**: Automatic report generation
- 🔄 **Continuous Learning**: Add knowledge without restart
- 📤 **Multi-Format Upload**: CSV, PDF, DOCX, XLSX support
- 💬 **Interactive Agent**: Context-aware conversational AI
- 📈 **Analytics**: Real-time graphs and forecasting

### Technical Features

- ⚡ **Intel Optimized**: Leverages Xeon CPU capabilities (DL Boost, AVX-512, MKL)
- 🔐 **Enterprise Security**: JWT auth, encryption, rate limiting
- 🐳 **Fully Dockerized**: One-command deployment
- ☸️ **Kubernetes Ready**: Helm charts and GMC support
- 📊 **Production Features**: Health checks, logging, monitoring
- 🔁 **WebSocket Support**: Real-time updates
- 💾 **Persistent Storage**: Redis + PostgreSQL

## Getting Started

### Prerequisites

#### For Docker Compose Deployment

- **Intel Xeon Server** (3rd Gen or newer recommended)
- Docker 24.0+ and Docker Compose 2.0+
- 16GB+ RAM (32GB recommended)
- 50GB+ disk space (SSD recommended)
- HuggingFace API token

#### For Kubernetes Deployment

- Kubernetes cluster 1.24+
- kubectl configured
- Helm 3.0+ (for Helm deployment)
- GMC installed (for GMC deployment)

### Quick Start

1. **Clone the repository**:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/CogniwareIMS
```

2. **Download sample data** (Required):

```bash
./scripts/download-data.sh
```

This downloads 7,479 CSV files (~32MB) with Intel product specifications.

3. **Set environment**:

```bash
export HUGGINGFACEHUB_API_TOKEN="your-token-here"
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
```

4. **Build Docker images**:

```bash
cd docker_build_image
docker compose -f build.yaml build
```

5. **Deploy with Docker Compose**:

```bash
cd ../docker_compose/intel/xeon
source ./set_env.sh
docker compose up -d
```

6. **Access the application**:

- Frontend UI: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- RedisInsight: http://localhost:8001

7. **Initialize knowledge base**:

```bash
docker exec -it cogniwareims-backend python app/init_knowledge_base.py
```

## Deployment

### Docker Compose Deployment

#### Intel Xeon Processors

```bash
cd docker_compose/intel/xeon
source ./set_env.sh
docker compose up -d
```

**Verify deployment**:

```bash
# Check all services
docker compose ps

# Test backend
curl http://localhost:8000/api/health

# View logs
docker compose logs -f cogniwareims-backend
```

For detailed Docker Compose instructions, see [docker_compose/README.md](docker_compose/README.md).

### Kubernetes Deployment with Helm

```bash
# Create namespace
kubectl create namespace opea

# Install with Helm
helm install cogniwareims ./kubernetes/helm \
  --namespace opea \
  --set global.HUGGINGFACEHUB_API_TOKEN=<your-token>

# Check deployment
kubectl get pods -n opea
kubectl get svc -n opea

# Access UI
kubectl port-forward -n opea svc/cogniwareims-ui 3000:3000
```

For detailed Kubernetes instructions, see [kubernetes/README.md](../kubernetes/README.md).

### Kubernetes Deployment with GMC

```bash
# Install GMC (if not installed)
kubectl apply -f https://github.com/opea-project/GenAIInfra/releases/download/v1.0/gmc.yaml

# Deploy CogniwareIMS
kubectl apply -f kubernetes/gmc/cogniwareims.yaml

# Verify
kubectl get gmconnector cogniwareims
kubectl get pods -l app=cogniwareims
```

## Usage

### Interactive Chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What Intel processors are good for inventory systems?",
    "session_id": "user_123",
    "user_role": "Inventory Manager"
  }'
```

### Natural Language Database Query

```bash
curl -X POST http://localhost:8000/api/inventory/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all Xeon 6 processors in San Jose warehouse"
  }'
```

### Upload Knowledge

```bash
# Upload CSV file
curl -X POST http://localhost:8000/api/knowledge/upload-file \
  -F "file=@product_catalog.csv"

# Add text knowledge
curl -X POST http://localhost:8000/api/knowledge/add \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Intel Xeon 6 Processor - 64 cores, 2.5GHz base, 4.0GHz boost",
    "source": "product_catalog",
    "metadata": {"category": "processors"}
  }'
```

### Document Summarization

```bash
curl -X POST http://localhost:8000/api/documents/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Long inventory report text...",
    "summary_type": "bullet_points",
    "max_length": 150
  }'
```

### Get Analytics

```bash
# Stock trends
curl http://localhost:8000/api/graphs/stock-trend/CPU-XN6-2024?days=30

# Category distribution
curl http://localhost:8000/api/graphs/category-distribution

# Performance metrics
curl http://localhost:8000/api/graphs/performance-metrics
```

## Testing

### Run E2E Tests

**Docker Compose Test**:

```bash
./tests/test_compose_on_xeon.sh
```

**Kubernetes GMC Test**:

```bash
./tests/test_gmc_on_xeon.sh
```

### Health Checks

```bash
# Check all services
./scripts/health_check.sh

# Individual checks
curl http://localhost:8000/api/health
curl http://localhost:6000/v1/health  # Embedding
curl http://localhost:9000/v1/health  # LLM
```

For detailed testing instructions, see [tests/README.md](../tests/README.md).

## Contributing

We welcome contributions! Please follow these steps:

1. **Read the guidelines**: See [CONTRIBUTING.md](CONTRIBUTING.md)
2. **Fork the repository**
3. **Create a feature branch**: `git checkout -b feature/amazing-feature`
4. **Commit with sign-off**: `git commit -s -m 'Add amazing feature'`
5. **Push to branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Developer Certificate of Origin

All commits must be signed off with the `-s` flag:

```bash
git commit -s -m "Your commit message"
```

## Support

### Documentation

- [OPEA Documentation](https://opea-project.github.io)
- [Architecture Guide](../assets/README.md)
- [Deployment Guide](../kubernetes/README.md)
- [Testing Guide](../tests/README.md)
- [Data Setup Guide](DATA_SETUP.md)

### Getting Help

- **GitHub Issues**: [Report bugs or request features](https://github.com/opea-project/GenAIExamples/issues)
- **Email**: info@opea.dev
- **Community**: [OPEA Discussions](https://github.com/opea-project/discussions)

### Troubleshooting

**Services not starting**:

```bash
# Check logs
docker compose logs <service-name>

# Verify resources
docker stats

# Check ports
netstat -tulpn | grep -E '3000|6000|8000'
```

**Performance issues**:

- Ensure 16GB+ RAM available
- Use SSD storage for better I/O
- Verify Intel Xeon optimizations are enabled
- Check model sizes in configuration

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](../LICENSE) file for details.

## Acknowledgments

- [OPEA Project](https://github.com/opea-project) - Open Platform for Enterprise AI
- [GenAIComps](https://github.com/opea-project/GenAIComps) - GenAI Microservices
- Intel Corporation - For neural-chat models and optimization
- BAAI - For BGE embedding models
- **CogniDREAM** - Cogniware AI Code Generation Platform

## Technology Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: Python, FastAPI, OPEA Comps
- **AI/ML**: HuggingFace TGI, TEI, Sentence Transformers
- **Databases**: PostgreSQL, Redis with vector search
- **Deployment**: Docker, Kubernetes, Helm
- **Optimization**: Intel DL Boost, AVX-512, MKL, OpenMP

---

**Built with ❤️ using OPEA GenAI Components and CogniDREAM Platform**

_Production-ready • Scalable • Secure • AI-Powered • Intel Optimized_

For more examples and use cases, visit [OPEA GenAI Examples](https://github.com/opea-project/GenAIExamples).

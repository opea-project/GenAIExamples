# CogniwareIMS - AI-Powered Inventory Management System

[![OPEA](https://img.shields.io/badge/OPEA-GenAI%20Components-blue)](https://github.com/opea-project/GenAIComps)
[![Intel](https://img.shields.io/badge/Intel-Xeon%20Optimized-0071C5?logo=intel)](https://www.intel.com/content/www/us/en/products/details/processors/xeon.html)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)

## Overview

**CogniwareIMS** is a production-ready, AI-powered Inventory Management System built on the [OPEA (Open Platform for Enterprise AI)](https://github.com/opea-project) framework, specifically optimized for Intel Xeon processors. It demonstrates enterprise-grade integration of multiple GenAI microservices for intelligent inventory operations.

Built with **CogniDREAM Code Generation Platform**, a Cogniware AI engine for creating production-ready agentic platforms.

## Key Features

- 🤖 **AI-Powered Queries**: Natural language inventory search using RAG (Retrieval-Augmented Generation)
- 📊 **DBQnA Agent**: Convert natural language to SQL for database queries
- 📝 **Document Summarization**: Automatic report generation and analysis
- 🔄 **Continuous Learning**: Add new knowledge and retrain models in real-time
- 📤 **Multi-Format Upload**: Upload CSV, XLSX, PDF, DOCX files directly to knowledge base
- 💬 **Interactive Agent**: Context-aware conversational AI for inventory management
- 📈 **Real-time Analytics**: Dynamic graphs, forecasting, and performance metrics
- 🐳 **Fully Dockerized**: One-command deployment with Docker Compose
- ⚡ **Intel Optimized**: Leverages Intel Xeon CPU capabilities for maximum performance

## Quick Start

### Prerequisites

- Docker 24.0+ and Docker Compose 2.0+
- 16GB RAM minimum (32GB recommended)
- 50GB free disk space
- HuggingFace API token (for model downloads)

### Step 1: Set Environment Variables

```bash
export HUGGINGFACEHUB_API_TOKEN=your_token_here
```

### Step 2: Download Sample Data

```bash
./scripts/download-data.sh
```

### Step 3: Deploy with Docker Compose

```bash
cd docker_compose/intel/cpu/xeon
docker compose up -d
```

### Step 4: Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Testing

Run the end-to-end test:

```bash
cd tests
export HUGGINGFACEHUB_API_TOKEN=your_token_here
./test_compose_on_xeon.sh
```

## Architecture

This system uses the OPEA megaservice pattern to orchestrate multiple microservices:

- **LLM Microservice**: Text generation (Intel/neural-chat-7b-v3-3)
- **Embedding Microservice**: Text vectorization (BAAI/bge-base-en-v1.5)
- **Retriever Microservice**: Vector search with Redis
- **Reranking Microservice**: Improve retrieval quality (BAAI/bge-reranker-base)
- **DataPrep Microservice**: Document ingestion and processing

## License

Apache 2.0 - See [LICENSE](LICENSE) file for details.

## Support

For issues and questions, please open an issue in the OPEA GenAIExamples repository.

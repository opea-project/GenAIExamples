# Cogniware OPEA IMS - AI-Powered Inventory Management System

[![OPEA](https://img.shields.io/badge/OPEA-GenAI%20Components-blue)](https://github.com/opea-project/GenAIComps)
[![Intel](https://img.shields.io/badge/Intel-Xeon%20Optimized-0071C5?logo=intel)](https://www.intel.com/content/www/us/en/products/details/processors/xeon.html)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![Production](https://img.shields.io/badge/Status-Production%20Ready-success)](https://github.com/opea-project)

## 🎯 Overview

**Cogniware OPEA IMS** is a production-ready, AI-powered Inventory Management System built on the [OPEA (Open Platform for Enterprise AI)](https://github.com/opea-project) framework, **specifically optimized for Intel Xeon processors**. It demonstrates enterprise-grade integration of multiple GenAI microservices for intelligent inventory operations, leveraging Intel's AI acceleration capabilities for superior performance. This platform is built with CogniDREAM Code Generation Platform, a Cogniware AI engine that can create end-to-end production ready agentic platforms with natural language inputs.

> **🚀 Intel Xeon Powered**: This system is engineered to leverage Intel Xeon processor capabilities including:
>
> - Intel Deep Learning Boost (Intel DL Boost) for faster AI inference
> - Intel Advanced Vector Extensions (AVX-512) for optimized computations
> - Intel Math Kernel Library (MKL) integration for superior performance
> - Optimized threading with Intel OpenMP (KMP) for parallel processing
> - No NVIDIA GPU required - runs efficiently on CPU-only infrastructure

### Key Features

- 🤖 **AI-Powered Queries**: Natural language inventory search using RAG (Retrieval-Augmented Generation)
- 📊 **DBQnA Agent**: Convert natural language to SQL for database queries
- 📝 **Document Summarization**: Automatic report generation and analysis
- 🔄 **Continuous Learning**: Add new knowledge and retrain models in real-time
- 📤 **Multi-Format Upload**: Upload CSV, XLSX, PDF, DOCX files directly to knowledge base
- 💬 **Interactive Agent**: Context-aware conversational AI for inventory management
- 📈 **Real-time Analytics**: Dynamic graphs, forecasting, and performance metrics
- 🔐 **Enterprise Security**: Industry-standard authentication, encryption, and access control
- 🐳 **Fully Dockerized**: One-command deployment with Docker Compose
- ⚡ **Intel Optimized**: Leverages Intel Xeon CPU capabilities for maximum performance

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│  Modern UI • Real-time Updates • Interactive Dashboards     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API (FastAPI)                           │
│  Authentication • Business Logic • API Gateway              │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│               OPEA GenAI Microservices                       │
├─────────────────┬──────────────┬──────────────┬─────────────┤
│  Embedding      │  Retrieval   │  LLM         │  ChatQnA    │
│  Service        │  Service     │  Service     │  Gateway    │
│  (Port 6000)    │  (Port 7000) │  (Port 9000) │  (Port 8888)│
└─────────────────┴──────────────┴──────────────┴─────────────┘
          │                              │
          ▼                              ▼
┌──────────────────┐         ┌──────────────────────┐
│  Redis Vector    │         │  PostgreSQL          │
│  Store           │         │  Database            │
└──────────────────┘         └──────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Intel Xeon Server** (3rd Gen or newer recommended)
- Docker 24.0+ and Docker Compose 2.0+
- 16GB RAM minimum (32GB recommended for production)
- 50GB free disk space (SSD recommended)
- **Optimized for Intel Xeon processors** - leverages Intel optimizations for AI workloads

### Step 1: Download Sample Data

> **⚠️ Important**: The sample data files (7,479 CSV files, ~32MB) are **not included** in the Git repository per OPEA guidelines. They must be downloaded separately before first use.

**Automated download (recommended)**:

```bash
# Download sample inventory data
./scripts/download-data.sh
```

**Manual download**:
See [Data Setup Guide](docs/DATA_SETUP.md) for detailed instructions and alternative download options.

**What's included**:

- 7,479 CSV files with Intel product specifications
- Product categories: Xeon processors, Core CPUs, FPGAs, server components, storage, networking
- Total size: ~32 MB compressed, ~45 MB extracted

### Step 2: One-Command Deployment

```bash
# Clone or download this package
cd cogniware-opea-ims

# Start all services
./start.sh

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Step 3: Initialize Knowledge Base

```bash
# In a new terminal, initialize with CSV data (7,479+ documents)
docker-compose exec backend python app/init_knowledge_base.py

# Verify initialization
curl http://localhost:8000/api/knowledge/stats
```

## 📦 What's Included

### Core Services

1. **Frontend Application** (Next.js 14)

   - Modern, responsive UI with Tailwind CSS
   - Real-time chat interface
   - Interactive dashboards and analytics
   - Knowledge management interface

2. **Backend API** (FastAPI)

   - RESTful API endpoints
   - WebSocket support for real-time updates
   - Comprehensive error handling
   - API documentation (OpenAPI/Swagger)

3. **OPEA Microservices**

   - **Embedding Service**: Text vectorization (BAAI/bge-base-en-v1.5)
   - **Retrieval Service**: Semantic search with Redis
   - **LLM Service**: Text generation (Intel/neural-chat-7b-v3-3)
   - **ChatQnA Gateway**: Orchestration and routing

4. **Data Layer**
   - PostgreSQL: Relational database for structured data
   - Redis: Vector store and caching
   - CSV Data: 286+ files with 15,000+ documents

### Security Features

- ✅ JWT-based authentication
- ✅ HTTPS/TLS encryption support
- ✅ API rate limiting
- ✅ CORS protection
- ✅ Input validation and sanitization
- ✅ SQL injection prevention
- ✅ Secure password hashing
- ✅ Environment-based secrets management

### Production Features

- ✅ Health check endpoints
- ✅ Structured logging
- ✅ Error tracking and monitoring
- ✅ Graceful shutdown
- ✅ Auto-restart on failure
- ✅ Resource limits and quotas
- ✅ Horizontal scaling support

## 🔧 Configuration

### Environment Variables

Copy and customize the environment file:

```bash
cp .env.example .env
# Edit .env with your settings
```

Key variables:

- `OPEA_EMBEDDING_URL`: Embedding service endpoint
- `OPEA_LLM_URL`: LLM service endpoint
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: Secret for JWT tokens (generate strong key!)
- `ALLOWED_ORIGINS`: CORS allowed origins

## 📖 Usage Guide

### 1. User Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"inventory@company.com","password":"password123"}'
```

**Default Users:**

- `consumer@company.com` - Consumer role
- `inventory@company.com` - Inventory Manager role
- `admin@company.com` - Super Admin role

### 2. AI-Powered Inventory Queries

```bash
# Natural language query
curl -X POST http://localhost:8000/api/inventory/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Show me all Xeon 6 processors in San Jose warehouse"}'
```

### 3. Interactive Chat

```bash
# Chat with AI agent
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What high-performance processors are low in stock?",
    "session_id": "user_123",
    "user_role": "Inventory Manager"
  }'
```

### 4. Add New Knowledge

```bash
# Add text knowledge
curl -X POST http://localhost:8000/api/knowledge/add \
  -H "Content-Type: application/json" \
  -d '{
    "text": "AMD EPYC 9654 - 96 cores, 2.4GHz base, 3.7GHz boost",
    "source": "product_catalog",
    "metadata": {"category": "processors"}
  }'
```

### 5. Document Summarization

```bash
# Summarize document
curl -X POST http://localhost:8000/api/documents/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Long inventory report text...",
    "summary_type": "bullet_points",
    "max_length": 150
  }'
```

## 🏗️ Architecture Details

### OPEA GenAI Components Integration

This system integrates the following OPEA components:

1. **Embeddings** (`comps/embeddings`)

   - Model: BAAI/bge-base-en-v1.5
   - Dimension: 768
   - Use: Text vectorization for semantic search

2. **Retrievers** (`comps/retrievers`)

   - Backend: Redis vector store
   - Algorithm: Cosine similarity
   - Use: Find relevant documents

3. **LLMs** (`comps/llms`)

   - Model: Intel/neural-chat-7b-v3-3
   - Use: Text generation, chat, SQL generation

4. **ChatQnA Megaservice**
   - Orchestrates: Embedding → Retrieval → LLM
   - Pattern: RAG (Retrieval-Augmented Generation)

### Data Flow

**Query Processing:**

```
User Query → Frontend
    ↓
Backend API validates & routes
    ↓
Interactive Agent orchestrates:
    ├→ Embedding Service (vectorize query)
    ├→ Retrieval Service (find relevant docs)
    ├→ DBQnA (generate SQL if needed)
    └→ LLM Service (generate response)
    ↓
Formatted response → Frontend → User
```

**Knowledge Ingestion:**

```
CSV/Text Input → Backend
    ↓
Knowledge Manager processes
    ├→ Parse & extract
    ├→ Embedding Service (generate vectors)
    └→ Retrieval Service (index in Redis)
    ↓
Immediately searchable
```

## 📊 API Reference

### Core Endpoints

- `POST /api/auth/login` - User authentication
- `POST /api/chat` - Interactive chat with AI agent
- `POST /api/inventory/query` - Natural language inventory query
- `GET /api/health` - System health check

### Knowledge Management

- `POST /api/knowledge/add` - Add knowledge text
- `POST /api/knowledge/upload-csv` - Upload CSV file
- `POST /api/knowledge/retrain` - Retrain knowledge base
- `GET /api/knowledge/stats` - Get statistics
- `GET /api/knowledge/search` - Search knowledge base

### Analytics & Graphs

- `GET /api/graphs/stock-trend/{sku}` - Stock level trends
- `GET /api/graphs/category-distribution` - Product categories
- `GET /api/graphs/warehouse-comparison` - Warehouse metrics
- `GET /api/graphs/performance-metrics` - KPIs

**Full API Documentation:** http://localhost:8000/docs

## 🧪 Testing

### Health Checks

```bash
# Check all services
./scripts/health_check.sh

# Individual service checks
curl http://localhost:8000/api/health
curl http://localhost:6000/v1/health_check  # Embedding
curl http://localhost:9000/v1/health_check  # LLM
```

### End-to-End Test

```bash
# Run comprehensive test suite
./scripts/test_e2e.sh
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test API endpoint
ab -n 1000 -c 10 http://localhost:8000/api/health
```

## 🔒 Security Best Practices

### Production Deployment Checklist

- [ ] Change all default passwords
- [ ] Generate strong JWT secret key
- [ ] Enable HTTPS/TLS with valid certificates
- [ ] Configure firewall rules
- [ ] Set up rate limiting
- [ ] Enable API authentication for all endpoints
- [ ] Implement audit logging
- [ ] Regular security updates
- [ ] Data backup strategy
- [ ] Disaster recovery plan

### Secrets Management

```bash
# Generate secure JWT secret
openssl rand -hex 32

# Set in .env file
JWT_SECRET_KEY=<generated-secret>

# Never commit .env to version control!
```

## 📈 Monitoring & Logging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f embedding-service

# Save logs to file
docker-compose logs > logs.txt
```

### Metrics

Access metrics at:

- Prometheus: http://localhost:9090 (if enabled)
- Grafana: http://localhost:3001 (if enabled)

## 🔄 Maintenance

### Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres opea_ims > backup.sql

# Backup knowledge base
curl http://localhost:8000/api/knowledge/export > knowledge_backup.json

# Backup Redis
docker-compose exec redis redis-cli SAVE
```

### Updates

```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build

# Verify
./scripts/health_check.sh
```

### Scaling

```bash
# Scale backend instances
docker-compose up -d --scale backend=3

# Scale with load balancer (nginx)
# See docs/scaling.md
```

## 🌟 Use Cases

### 1. Intelligent Inventory Search

"Show me all GPUs with more than 40GB memory in stock at Portland warehouse"

### 2. Automated Reporting

"Generate a summary of this month's inventory movements"

### 3. Predictive Analytics

"Forecast demand for Xeon processors for next 30 days"

### 4. Natural Language Database Queries

"Which products are below reorder threshold?"

### 5. Continuous Learning

Upload new product catalogs, system automatically learns and adapts

## 📚 Documentation

- **[Data Setup Guide](docs/DATA_SETUP.md)** - ⚠️ **Required**: Download sample data files
- [Data Source Updates](docs/DATA_SOURCE_UPDATE.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Submission Checklist](docs/SUBMISSION_CHECKLIST.md)
- [Final Submission Checklist](docs/FINAL_SUBMISSION_CHECKLIST.md)
- [Ready for Submission Guide](docs/READY_FOR_SUBMISSION.md)
- [Security Guidelines](docs/SECURITY.md)
- [Security Updates](docs/SECURITY_UPDATES.md) - Recent CVE fixes
- [Changelog](docs/CHANGELOG.md)
- [Compliance Summary](docs/OPEA_COMPLIANCE_SUMMARY.md)
- [How to Submit](docs/HOW_TO_SUBMIT_TO_OPEA.md)

## 🤝 Contributing

This project follows OPEA contribution guidelines. See [CONTRIBUTING.md](docs/CONTRIBUTING.md).

### Development Setup

```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend development
cd frontend
npm install
npm run dev

# Run tests
cd backend && pytest
cd frontend && npm test
```

## 📄 License

This project is licensed under the Apache License 2.0 - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- [OPEA Project](https://github.com/opea-project) - Open Platform for Enterprise AI
- [GenAIComps](https://github.com/opea-project/GenAIComps) - GenAI Microservices
- Intel Corporation - For neural-chat models
- BAAI - For BGE embedding models

## 📞 Support

- Documentation: [docs/](docs/)
- Issues: GitHub Issues
- OPEA Community: [opea-project discussions](https://github.com/opea-project/discussions)

## 🎯 Roadmap

- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Mobile application
- [ ] Integration with ERP systems
- [ ] ML-based demand forecasting
- [ ] Blockchain for supply chain tracking

---

**Built with ❤️ using OPEA GenAI Components**

_Production-ready • Scalable • Secure • AI-Powered_

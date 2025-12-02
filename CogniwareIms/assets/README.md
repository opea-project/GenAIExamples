# Cogniware IMS Architecture Assets

This directory contains architecture diagrams and documentation for the OPEA Cogniware Inventory Management System.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│  Modern UI • File Upload • Real-time Chat • Dashboards     │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API / WebSocket
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API (FastAPI)                           │
│  Authentication • Business Logic • Session Management       │
└─────────┬───────────────────────────────────────────────────┘
          │
          ├──────────────────┬──────────────────┐
          ▼                  ▼                  ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│  Interactive   │  │   Knowledge    │  │     DBQnA      │
│     Agent      │  │    Manager     │  │    Service     │
│ (RAG + Chat)   │  │ (Continuous    │  │  (NL → SQL)    │
│                │  │   Learning)    │  │                │
└────────────────┘  └────────────────┘  └────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 OPEA Microservices Layer                     │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Embedding │─▶│Retriever │─▶│ Rerank   │─▶│   LLM    │   │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │   │
│  │(Port 6000)  │(Port 7000)  │(Port 8000)  │(Port 9000)  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │              DataPrep Service                     │       │
│  │         (Document Processing & Indexing)          │       │
│  │                  (Port 6007)                      │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
┌──────────────────┐         ┌──────────────────────┐
│  Redis Vector    │         │  PostgreSQL          │
│  Store + Cache   │         │  Database            │
│  (Port 6379)     │         │  (Port 5432)         │
└──────────────────┘         └──────────────────────┘
```

## Key Features

### 1. RAG Pipeline (Retrieval-Augmented Generation)

```
User Query
    │
    ▼
Embedding Service (Text → Vector)
    │
    ▼
Retriever Service (Vector Search in Redis)
    │
    ▼
Rerank Service (Improve Relevance)
    │
    ▼
LLM Service (Generate Response with Context)
    │
    ▼
Formatted Response to User
```

### 2. Continuous Learning Pipeline

```
New Data Upload (CSV, PDF, DOCX, XLSX)
    │
    ▼
Knowledge Manager (Parse & Extract)
    │
    ▼
Embedding Service (Generate Vectors)
    │
    ▼
Retriever Service (Index in Redis)
    │
    ▼
Immediately Searchable in RAG Pipeline
```

### 3. DBQnA Pipeline (Natural Language to SQL)

```
Natural Language Question
    │
    ▼
DBQnA Service
    │
    ├─▶ LLM Service (Generate SQL)
    │
    ├─▶ PostgreSQL (Execute Query)
    │
    └─▶ Format Results
    │
    ▼
Structured Answer to User
```

## Component Details

### Frontend Layer (Port 3000)

**Technology**: Next.js 14 with TypeScript

**Features**:

- File upload interface (CSV, PDF, DOCX, XLSX)
- Real-time chat with AI agents
- Knowledge base management
- Analytics dashboards
- Responsive design

### Backend Layer (Port 8000)

**Technology**: FastAPI with Python

**Services**:

- **Interactive Agent**: Context-aware conversational AI
- **Knowledge Manager**: Document processing and continuous learning
- **DBQnA Service**: Natural language to SQL conversion
- **Doc Summarization**: Automatic report generation
- **Graph Generator**: Analytics and visualization data
- **CSV Processor**: Batch data processing
- **File Upload Service**: Multi-format document handling

### OPEA Microservices Layer

#### Embedding Service (Port 6000)

- Model: BAAI/bge-base-en-v1.5
- Dimension: 768
- Purpose: Text vectorization for semantic search

#### Retriever Service (Port 7000)

- Backend: Redis vector store
- Algorithm: Cosine similarity
- Purpose: Semantic search in knowledge base

#### Reranking Service (Port 8000)

- Model: BAAI/bge-reranker-base
- Purpose: Improve retrieval relevance

#### LLM Service (Port 9000)

- Model: Intel/neural-chat-7b-v3-3
- Purpose: Text generation, chat, SQL generation
- Optimization: Intel Xeon processors

#### DataPrep Service (Port 6007)

- Purpose: Document ingestion and indexing
- Formats: CSV, PDF, DOCX, XLSX, TXT

### Data Layer

#### Redis (Port 6379)

- Vector search with RediSearch
- Session caching
- Real-time data storage

#### PostgreSQL (Port 5432)

- Relational data storage
- Inventory records
- User management
- Transaction logs

## Data Flow Examples

### Example 1: Chat Query

```
User: "What Intel processors are low in stock?"
    ↓
Backend receives query
    ↓
Interactive Agent orchestrates:
  1. Embedding Service: Convert query to vector
  2. Retriever Service: Find relevant inventory docs
  3. Reranking Service: Rank by relevance
  4. LLM Service: Generate natural language response
    ↓
Response: "Based on current inventory, the following Intel processors are below reorder threshold: [list]"
```

### Example 2: File Upload

```
User uploads: product_catalog.csv
    ↓
File Upload Service validates format
    ↓
CSV Processor extracts records
    ↓
Knowledge Manager processes:
  1. Parse CSV into structured data
  2. Generate text descriptions
  3. Embedding Service: Create vectors
  4. Retriever Service: Index in Redis
    ↓
Status: "Successfully indexed 500 products. Knowledge base updated."
```

### Example 3: Natural Language Database Query

```
User: "Show inventory value by warehouse"
    ↓
DBQnA Service:
  1. Get database schema
  2. LLM generates SQL:
     SELECT warehouse, SUM(value)
     FROM inventory
     GROUP BY warehouse
  3. Execute on PostgreSQL
  4. Format results
    ↓
Response: Table with warehouse inventory values
```

## Intel Xeon Optimizations

This system is optimized for Intel Xeon processors:

1. **Intel DL Boost**: Accelerated AI inference
2. **AVX-512**: Vector instructions for faster computations
3. **Intel MKL**: Optimized math libraries
4. **OpenMP**: Parallel processing with KMP settings
5. **Memory Optimizations**: jemalloc for better memory management

Environment variables for optimization:

```bash
OMP_NUM_THREADS=8
KMP_AFFINITY=granularity=fine,compact,1,0
KMP_BLOCKTIME=1
MALLOC_CONF=oversize_threshold:1,background_thread:true
```

## Deployment Architectures

### Docker Compose Deployment

```
Single Host (Intel Xeon Server)
├── All services in Docker containers
├── Docker network for inter-service communication
├── Persistent volumes for data
└── Health checks and auto-restart
```

### Kubernetes Deployment

```
Kubernetes Cluster
├── Frontend: 2+ replicas (LoadBalancer)
├── Backend: 3+ replicas (ClusterIP)
├── Microservices: 1+ replicas each
├── Databases: StatefulSets with PVCs
├── HPA: Auto-scaling based on CPU/memory
└── Ingress: External access with SSL/TLS
```

## Security Architecture

1. **Authentication**: JWT-based tokens
2. **Authorization**: Role-based access control
3. **Encryption**: TLS/SSL for data in transit
4. **Database**: Password protection, encrypted connections
5. **API**: Rate limiting, input validation
6. **Secrets**: Environment variables, K8s secrets

## Monitoring & Observability

### Metrics

- Request rates and latencies
- Model inference times
- Database query performance
- Resource utilization (CPU, memory)

### Logging

- Structured logs with timestamps
- Service-level logging
- Error tracking
- Audit logs

### Health Checks

- `/api/health` - Overall system health
- `/v1/health` - Individual microservice health
- Database connectivity checks
- Model loading status

## Performance Characteristics

### Latency (Intel Xeon 3rd Gen+)

- Embedding generation: ~50-100ms
- Vector search: ~10-30ms
- LLM inference: ~1-3s (depending on response length)
- End-to-end query: ~2-5s

### Throughput

- Concurrent requests: 50-100 (with proper scaling)
- Documents processed: 100-500/minute
- Vector indexing: 1000+ docs/minute

### Resource Requirements

- **Minimum**: 16GB RAM, 4 CPU cores
- **Recommended**: 32GB RAM, 8 CPU cores
- **Production**: 64GB RAM, 16+ CPU cores, SSD storage

## Notes

For actual visual diagrams (PNG/SVG), use tools like:

- draw.io / diagrams.net
- Lucidchart
- Mermaid

Recommended diagrams to create:

- `architecture-overview.png` - High-level system design
- `rag-pipeline-flow.png` - RAG processing flow
- `deployment-topology.png` - Infrastructure layout
- `data-flow-diagram.png` - Complete data flow

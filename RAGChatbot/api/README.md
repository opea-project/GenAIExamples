# RAG Chatbot API

A production-ready RAG (Retrieval-Augmented Generation) chatbot API built with FastAPI, LangChain, and FAISS for document-based question answering.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## Features

- Clean PDF upload with validation
- LangChain-powered document processing
- FAISS-CPU vector store for efficient similarity search
- Enterprise inference endpoints for embeddings and LLM
- Keycloak authentication for secure API access
- Comprehensive error handling and logging
- File validation and size limits
- CORS enabled for web integration
- Health check endpoints
- Modular architecture (routes + services)

## Quick Start

Get up and running in 3 minutes using Docker Compose:

```bash
# 1. Navigate to the rag-chatbot directory
cd /path/to/rag-chatbot

# 2. Create .env file in the api directory with enterprise configuration
mkdir -p api
cat > api/.env << EOF
BASE_URL=https://api.example.com
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=api
KEYCLOAK_CLIENT_SECRET=your_client_secret
EMBEDDING_MODEL_ENDPOINT=bge-base-en-v1.5
INFERENCE_MODEL_ENDPOINT=Llama-3.1-8B-Instruct
EMBEDDING_MODEL_NAME=bge-base-en-v1.5
INFERENCE_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
EOF

# 3. Start both API and UI services with Docker Compose
docker compose up --build

# 4. Access the application
# API: http://localhost:5001/docs
# UI: http://localhost:3000
```

The application will automatically start both the backend API and frontend UI. Visit http://localhost:5001/docs for interactive API documentation.

## Installation

### Prerequisites

- Docker and Docker Compose installed
- Enterprise inference endpoint access (Keycloak authentication)

### Docker Compose Setup

Docker Compose will start both the API and UI services together.

1. **Set up environment variables**:

Create a `.env` file in the `api` directory (relative to `rag-chatbot/`):

```bash
cd rag-chatbot
mkdir -p api
cat > api/.env << EOF
# Backend API URL (accessible from frontend)
VITE_API_URL=https://backend:5000

# Required - Enterprise/Keycloak Configuration
BASE_URL=https://api.example.com
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=api
KEYCLOAK_CLIENT_SECRET=your_client_secret

# Required - Model Configuration
EMBEDDING_MODEL_ENDPOINT=bge-base-en-v1.5
INFERENCE_MODEL_ENDPOINT=Llama-3.1-8B-Instruct
EMBEDDING_MODEL_NAME=bge-base-en-v1.5
INFERENCE_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
EOF
```

2. **Start the services**:

```bash
# From the rag-chatbot directory
docker compose up --build
```

This will:
- Build the backend API container
- Build the frontend UI container
- Start both services automatically
- Make API available at http://localhost:5001
- Make UI available at http://localhost:3000

### Dependencies

The main dependencies include:

- `fastapi==0.109.0` - Web framework
- `uvicorn[standard]==0.27.0` - ASGI server
- `langchain==0.1.0` - LLM framework
- `faiss-cpu==1.7.4` - Vector similarity search
- `pypdf==4.0.1` - PDF processing

See `requirements.txt` for complete list.

## Configuration

All configuration is centralized in `config.py`. You can modify settings by editing this file or using environment variables.

### Environment Variables

For Docker Compose, create a `.env` file in the `api/` directory (relative to `rag-chatbot/`):

```bash
# Backend API URL (accessible from frontend)
VITE_API_URL=https://backend:5000

# Required - Enterprise/Keycloak Configuration
BASE_URL=https://api.example.com
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=api
KEYCLOAK_CLIENT_SECRET=your_client_secret

# Required - Model Configuration
EMBEDDING_MODEL_ENDPOINT=bge-base-en-v1.5
INFERENCE_MODEL_ENDPOINT=Llama-3.1-8B-Instruct
EMBEDDING_MODEL_NAME=bge-base-en-v1.5
INFERENCE_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct

# Optional (with defaults shown)
# VECTOR_STORE_PATH=./dmv_index
# MAX_FILE_SIZE_MB=50
```

**Note**: The docker-compose.yml file automatically loads environment variables from `./api/.env` for the backend service.

### Configuration Settings

Edit `config.py` to customize:

#### File Upload Settings

```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf"}
```

#### Text Processing Settings

```python
CHUNK_SIZE = 1000           # Characters per chunk
CHUNK_OVERLAP = 200         # Overlap between chunks
SEPARATORS = ["\n\n", "\n", " ", ""]  # Text splitting separators
```

#### Vector Store Settings

```python
VECTOR_STORE_PATH = "./dmv_index"  # Where to store FAISS index
```

#### LLM Settings

```python
LLM_TEMPERATURE = 0                      # Response randomness (0-1)
TOP_K_DOCUMENTS = 4                      # Documents to retrieve
# Model endpoints and names are configured via environment variables:
# EMBEDDING_MODEL_ENDPOINT, INFERENCE_MODEL_ENDPOINT
# EMBEDDING_MODEL_NAME, INFERENCE_MODEL_NAME
```

#### CORS Settings

```python
CORS_ALLOW_ORIGINS = ["*"]  # Update with specific origins in production
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]
```

## Running the Server

**Start both API and UI together**:

```bash
# From the rag-chatbot directory
docker compose up --build

# Or run in detached mode (background)
docker compose up -d --build
```

**Stop the services**:

```bash
docker compose down
```

The API will be available at: `http://localhost:5001`  
The UI will be available at: `http://localhost:3000`

**View logs**:

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Frontend only
docker compose logs -f frontend
```

### Verifying the Server

```bash
# Check if API server is running
curl http://localhost:5001/

# Check health status
curl http://localhost:5001/health

# Check if containers are running
docker compose ps
```

## API Endpoints

### Health Check

**GET /** - Basic health check

```bash
curl http://localhost:5001/
```

Response:

```json
{
  "message": "RAG Chatbot API is running",
  "version": "2.0.0",
  "status": "healthy",
  "vectorstore_loaded": true
}
```

**GET /health** - Detailed health status

```bash
curl http://localhost:5001/health
```

Response:

```json
{
  "status": "healthy",
  "vectorstore_available": true,
  "enterprise_inference_configured": true
}
```

### Upload PDF

**POST /upload-pdf** - Upload and process a PDF document

```bash
curl -X POST "http://localhost:5001/upload-pdf" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/document.pdf"
```

Response:

```json
{
  "message": "Successfully uploaded and processed 'document.pdf'",
  "num_chunks": 45,
  "status": "success"
}
```

**Validation Rules**:

- File must be PDF format
- Maximum size: 50MB (configurable)
- File must not be empty
- Content must be extractable

### Query Documents

**POST /query** - Ask questions about uploaded documents

```bash
curl -X POST "http://localhost:5001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main topics in the document?"}'
```

Response:

```json
{
  "answer": "The main topics covered in the document are...",
  "query": "What are the main topics in the document?"
}
```

### Delete Vector Store

**DELETE /vectorstore** - Delete the current vector store

```bash
curl -X DELETE "http://localhost:5001/vectorstore"
```

Response:

```json
{
  "message": "Vector store deleted successfully",
  "status": "success"
}
```

### Interactive API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:5001/docs
- **ReDoc**: http://localhost:5001/redoc

## Project Structure

The application follows a modular architecture with clear separation of concerns:

```
api/
├── server.py               # FastAPI app with routes (main entry point)
├── config.py               # Configuration settings
├── models.py               # Pydantic models for request/response validation
├── services/               # Business logic layer
│   ├── __init__.py
│   ├── pdf_service.py      # PDF processing and validation
│   ├── vector_service.py   # Vector store operations (FAISS)
│   └── retrieval_service.py # Query processing and LLM integration
├── requirements.txt        # Python dependencies
├── test_api.py            # Automated test suite
├── .env                   # Environment variables (create this)
└── dmv_index/             # FAISS vector store (auto-generated)
```

### Architecture Overview

```
Client Request
     ↓
server.py (Routes)
     ↓
models.py (Validation)
     ↓
services/ (Business Logic)
     ├── pdf_service.py
     ├── vector_service.py
     └── retrieval_service.py
     ↓
External Services (Enterprise Inference Endpoints, FAISS)
```

**Layered Architecture**:

- **Routes Layer** (`server.py`): HTTP handling, routing, error responses
- **Validation Layer** (`models.py`): Request/response validation
- **Business Logic Layer** (`services/`): Core functionality
- **Configuration Layer** (`config.py`): Settings management

## Testing

### Automated Test Suite

Run the included test suite:

```bash
# Basic tests (no PDF required)
python test_api.py

# Full tests with PDF upload
python test_api.py /path/to/your/document.pdf
```

The test suite includes:

- Health check tests
- Upload validation tests
- Query functionality tests
- Error handling tests
- Colored output for easy reading

### Manual Testing

1. **Start the services**:

```bash
docker compose up
```

2. **Upload a PDF**:

```bash
curl -X POST "http://localhost:5001/upload-pdf" \
  -F "file=@sample.pdf"
```

3. **Query the document**:

```bash
curl -X POST "http://localhost:5001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?"}'
```

4. **Check health**:

```bash
curl http://localhost:5001/health
```

## Development

### Project Setup for Development

1. Fork/clone the repository
2. Set up your `.env` file in the `api` directory
3. Run with Docker Compose for development: `docker compose up --build`
4. Make changes to code (changes are reflected with volume mounts in docker-compose.yml)

### Adding New Features

#### Add a New Service

1. Create new file in `services/` directory:

```python
# services/new_service.py
def new_function(param):
    """Your business logic"""
    return result
```

2. Export from `services/__init__.py`:

```python
from .new_service import new_function
```

3. Use in routes:

```python
# server.py
from services import new_function

@app.post("/new-endpoint")
def new_endpoint():
    result = new_function(data)
    return result
```

#### Add a New Endpoint

1. Define model in `models.py`:

```python
class NewRequest(BaseModel):
    field: str
```

2. Add route in `server.py`:

```python
@app.post("/new-endpoint")
def new_endpoint(request: NewRequest):
    # Your logic here
    return {"result": "success"}
```

### Modifying Configuration

Edit `config.py` to change default settings:

```python
# Example: Increase file size limit
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Example: Change chunk size
CHUNK_SIZE = 1500

# Example: Use different model
LLM_MODEL = "gpt-4"
```

### Code Style

- Use type hints for all functions
- Add docstrings to all public functions
- Follow PEP 8 style guide
- Keep functions focused (single responsibility)
- Log important operations

## Troubleshooting

### Common Issues

#### "Keycloak authentication or model endpoints not configured"

**Solution**:

1. Create a `.env` file in the `api` directory (relative to `rag-chatbot/`)
2. Add required configuration:
   ```bash
   BASE_URL=https://api.example.com
   KEYCLOAK_REALM=master
   KEYCLOAK_CLIENT_ID=api
   KEYCLOAK_CLIENT_SECRET=your_client_secret
   EMBEDDING_MODEL_ENDPOINT=bge-base-en-v1.5
   INFERENCE_MODEL_ENDPOINT=Llama-3.1-8B-Instruct
   EMBEDDING_MODEL_NAME=bge-base-en-v1.5
   INFERENCE_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
   ```
3. Restart the services with `docker compose restart backend` or `docker compose down && docker compose up`

#### "No documents uploaded"

**Solution**:

- Upload a PDF first using the `/upload-pdf` endpoint
- Check server logs for any upload errors
- Verify the PDF is not corrupted or empty

#### "Could not load vector store"

**Solution**:

- The vector store is created when you upload your first PDF
- Check that the application has write permissions in the directory
- Verify `dmv_index/` directory exists and is accessible

#### Import errors

**Solution**:

1. Rebuild the Docker containers: `docker compose down && docker compose build --no-cache && docker compose up`
2. Check container logs: `docker compose logs backend`

#### Server won't start

**Solution**:

1. Check if ports 5001 or 3000 are already in use: `lsof -i :5001` or `lsof -i :3000` (Unix) or `netstat -ano | findstr :5001` (Windows)
2. Check container logs: `docker compose logs backend`
3. Try rebuilding containers: `docker compose down && docker compose build --no-cache && docker compose up`
4. Check the logs for specific error messages

#### PDF upload fails

**Solution**:

1. Verify the file is a valid PDF
2. Check file size (must be under 50MB by default)
3. Ensure the PDF contains extractable text (not just images)
4. Check server logs for detailed error messages

#### Query returns no answer

**Solution**:

1. Verify a document has been uploaded successfully
2. Try rephrasing your question
3. Check if the document contains relevant information
4. Increase `TOP_K_DOCUMENTS` in `config.py` for broader search

### Logging

The application logs important events to the console:

- **INFO**: Normal operations (PDF processing, queries)
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors with stack traces

To view logs:

```bash
# View all logs
docker compose logs -f

# View backend logs only
docker compose logs -f backend
```

### Getting Help

1. View logs with `docker compose logs -f`
2. Visit the health endpoint: `http://localhost:5001/health`
3. Review the error messages in API responses
4. Check the interactive documentation: `http://localhost:5001/docs`

## Production Deployment

### Checklist

Before deploying to production:

- [ ] Configure secure `KEYCLOAK_CLIENT_SECRET`
- [ ] Set up proper `BASE_URL` for enterprise endpoints
- [ ] Configure specific CORS origins (not `["*"]`)
- [ ] Enable HTTPS
- [ ] Set up monitoring and alerting
- [ ] Configure logging to files
- [ ] Implement rate limiting
- [ ] Verify Keycloak authentication is working
- [ ] Set up backup for vector stores
- [ ] Configure firewall rules
- [ ] Use environment-specific configuration

### Docker Compose Production Deployment

The provided `docker-compose.yml` already includes both API and UI services. For production:

1. **Set up environment variables** in `api/.env`:

```bash
# Enterprise/Keycloak Configuration
BASE_URL=https://api.example.com
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=api
KEYCLOAK_CLIENT_SECRET=your_production_client_secret

# Model Configuration
EMBEDDING_MODEL_ENDPOINT=bge-base-en-v1.5
INFERENCE_MODEL_ENDPOINT=Llama-3.1-8B-Instruct
EMBEDDING_MODEL_NAME=bge-base-en-v1.5
INFERENCE_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
```

2. **Run in detached mode**:

```bash
docker compose up -d --build
```

3. **Monitor logs**:

```bash
docker compose logs -f
```

## License

MIT

## Support

For issues, questions, or contributions:

1. Check this README for solutions
2. Review the troubleshooting section
3. Check container logs: `docker compose logs -f`
4. Visit the interactive docs at `http://localhost:5001/docs`

---

**Version**: 2.0.0  
**Last Updated**: 2025  
**API Documentation**: http://localhost:5001/docs

## RAG Chatbot

A full-stack Retrieval-Augmented Generation (RAG) application that enables intelligent, document-based question answering.
The system integrates a FastAPI backend powered by LangChain, FAISS, and AI models, alongside a modern React + Vite + Tailwind CSS frontend for an intuitive chat experience.

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start Deployment](#quick-start-deployment)
- [User Interface](#user-interface)
- [Troubleshooting](#troubleshooting)
- [Additional Info](#additional-info)

---

## Project Overview

The **RAG Chatbot** demonstrates how retrieval-augmented generation can be used to build intelligent, document-grounded conversational systems. It retrieves relevant information from a knowledge base, passes it to a large language model, and generates a concise and reliable answer to the user’s query. This project integrates seamlessly with cloud-hosted APIs or local model endpoints, offering flexibility for research, enterprise, or educational use.

---

## Features

**Backend**

- Clean PDF upload with validation
- LangChain-powered document processing
- FAISS-CPU vector store for efficient similarity search
- Enterprise inference endpoints for embeddings and LLM
- Token-based authentication for inference API
- Comprehensive error handling and logging
- File validation and size limits
- CORS enabled for web integration
- Health check endpoints
- Modular architecture (routes + services)

**Frontend**

- PDF file upload with drag-and-drop support
- Real-time chat interface
- Modern, responsive design with Tailwind CSS
- Built with Vite for fast development
- Live status updates
- Mobile-friendly

---

## Architecture

Below is the architecture as it consists of a server that waits for documents to embed and index into a vector database. Once documents have been uploaded, the server will wait for user queries which initiates a similarity search in the vector database before calling the LLM service to summarize the findings.

![Architecture Diagram](./images/RAG%20Model%20System%20Design.png)

**Service Components:**

1. **React Web UI (Port 3000)** - Provides intuitive chat interface with drag-and-drop PDF upload, real-time messaging, and document-grounded Q&A interaction

2. **FastAPI Backend (Port 5001)** - Handles document processing, FAISS vector storage, LangChain integration, and orchestrates retrieval-augmented generation for accurate responses

**Typical Flow:**

1. User uploads a document through the web UI.
2. The backend processes the document by splitting it and transforming it into embeddings before storing it in the vector database.
3. User sends a question through the web UI.
4. The backend retrieves relevant content from stored documents.
5. The model generates a response based on retrieved context.
6. The answer is displayed to the user via the UI.

---

## Prerequisites

### System Requirements

Before you begin, ensure you have the following installed:

- **Docker and Docker Compose**
- **Enterprise inference endpoint access** (token-based authentication)

### Required API Configuration

**For Inference Service (RAG Chatbot):**

This application supports multiple inference deployment patterns:

- **GenAI Gateway**: Provide your GenAI Gateway URL and API key
- **APISIX Gateway**: Provide your APISIX Gateway URL and authentication token

Configuration requirements:
- INFERENCE_API_ENDPOINT: URL to your inference service (GenAI Gateway, APISIX Gateway, etc.)
- INFERENCE_API_TOKEN: Authentication token/API key for your chosen service

### Local Development Configuration

**For Local Testing Only (Optional)**

If you're testing with a local inference endpoint using a custom domain (e.g., `inference.example.com` mapped to localhost in your hosts file):

1. Edit `api/.env` and set:
   ```bash
   LOCAL_URL_ENDPOINT=inference.example.com
   ```
   (Use the domain name from your INFERENCE_API_ENDPOINT without `https://`)

2. This allows Docker containers to resolve your local domain correctly.

**Note:** For public domains or cloud-hosted endpoints, leave the default value `not-needed`.

### Verify Docker Installation

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker compose version

# Verify Docker is running
docker ps
```
---

## Quick Start Deployment

### Clone the Repository

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/RAGChatbot
```

### Set up the Environment

This application requires **two `.env` files** for proper configuration:

1. **Root `.env` file** (for Docker Compose variables)
2. **`api/.env` file** (for backend application configuration)

#### Step 1: Create Root `.env` File

```bash
# From the RAGChatbot directory
cat > .env << EOF
# Docker Compose Configuration
LOCAL_URL_ENDPOINT=not-needed
EOF
```

**Note:** If using a local domain (e.g., `inference.example.com` mapped to localhost), replace `not-needed` with your domain name (without `https://`).

#### Step 2: Create `api/.env` File

You can either copy from the example file:

```bash
cp api/.env.example api/.env
```

Then edit `api/.env` with your actual credentials, **OR** create it directly:

```bash
cat > api/.env << EOF
# Inference API Configuration
# INFERENCE_API_ENDPOINT: URL to your inference service (without /v1 suffix)
#   - For GenAI Gateway: https://genai-gateway.example.com
#   - For APISIX Gateway: https://apisix-gateway.example.com/inference
INFERENCE_API_ENDPOINT=https://your-actual-api-endpoint.com
INFERENCE_API_TOKEN=your-actual-token-here

# Model Configuration
# IMPORTANT: Use the full model names as they appear in your inference service
# Check available models: curl https://your-api-endpoint.com/v1/models -H "Authorization: Bearer your-token"
EMBEDDING_MODEL_NAME=BAAI/bge-base-en-v1.5
INFERENCE_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct

# Local URL Endpoint (for Docker)
LOCAL_URL_ENDPOINT=not-needed
EOF
```

**Important Configuration Notes:**

- **INFERENCE_API_ENDPOINT**: Your actual inference service URL (replace `https://your-actual-api-endpoint.com`)
- **INFERENCE_API_TOKEN**: Your actual pre-generated authentication token
- **EMBEDDING_MODEL_NAME** and **INFERENCE_MODEL_NAME**: Use the exact model names from your inference service
  - To check available models: `curl https://your-api-endpoint.com/v1/models -H "Authorization: Bearer your-token"`
- **LOCAL_URL_ENDPOINT**: Only needed if using local domain mapping (see [Local Development Configuration](#local-development-configuration))

**Note**: The docker-compose.yml file automatically loads environment variables from both `.env` (root) and `./api/.env` (backend) files.

### Running the Application

Start both API and UI services together with Docker Compose:

```bash
# From the RAGChatbot directory
docker compose up --build

# Or run in detached mode (background)
docker compose up -d --build
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

**Verify the services are running**:

```bash
# Check API health
curl http://localhost:5001/health

# Check if containers are running
docker compose ps
```

## User Interface

**Using the Application**

Make sure you are at the `http://localhost:3000` URL

You will be directed to the main page which has each feature

![User Interface](images/ui.png)

Upload a PDF:

- Drag and drop a PDF file, or
- Click "Browse Files" to select a file
- Wait for processing to complete

Start chatting:

- Type your question in the input field
- Press Enter or click Send
- Get AI-powered answers based on your document

**UI Configuration**

When running with Docker Compose, the UI automatically connects to the backend API. The frontend is available at `http://localhost:3000` and the API at `http://localhost:5001`.

For production deployments, you may want to configure a reverse proxy or update the API URL in the frontend configuration.

### Stopping the Application

```bash
docker compose down
```

## Troubleshooting

For comprehensive troubleshooting guidance, common issues, and solutions, refer to:

[Troubleshooting Guide - TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

## Additional Info

The following models have been validated with RAGChatbot:

| Model | Hardware |
|-------|----------|
| **meta-llama/Llama-3.1-8B-Instruct** | Gaudi |
| **BAAI/bge-base-en-v1.5** (embeddings) | Gaudi |
| **Qwen/Qwen3-4B-Instruct** | Xeon |

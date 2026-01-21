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
- Keycloak authentication for secure API access
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
- **Enterprise inference endpoint access** (Keycloak authentication)

### Verify Docker Installation

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker compose version

# Verify Docker is running
docker ps
```

## Quick Start Deployment

### Clone the Repository

```bash
git clone https://github.com/cld2labs/GenAISamples.git
cd GenAISamples/rag-chatbot
```

### Set up the Environment

This application requires an `.env` file in the `api` directory for proper configuration. Create it with the commands below:

```bash
# Create the .env file in the api directory
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

Or manually create `api/.env` with:

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
```

**Note**: The docker-compose.yml file automatically loads environment variables from `./api/.env` for the backend service.

### Running the Application

Start both API and UI services together with Docker Compose:

```bash
# From the rag-chatbot directory
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

Make sure you are at the localhost:3000 url

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

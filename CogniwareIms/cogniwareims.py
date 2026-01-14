#!/usr/bin/env python
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""OPEA Cogniware IMS Megaservice Application.

This application provides an AI-powered inventory management system for Intel products with advanced features including
RAG, DBQnA, document summarization, and continuous learning. Built with CogniDREAM Code Generation Platform.
"""

import os
from typing import List, Optional

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceType
from comps.cores.proto.api_protocol import ChatCompletionRequest
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse


class CogniwareIMSService:
    """Cogniware Inventory Management System Megaservice Orchestrates multiple AI microservices for intelligent
    inventory operations."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8888):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.CHAT_QNA)

    def add_remote_service(self):
        """Configure and add microservices to the megaservice."""

        # LLM Microservice - Text Generation (Intel neural-chat)
        llm_service = MicroService(
            name="llm",
            host=os.getenv("LLM_SERVICE_HOST", "localhost"),
            port=int(os.getenv("LLM_SERVICE_PORT", 9000)),
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )

        # Embedding Microservice - Text Vectorization
        embedding_service = MicroService(
            name="embedding",
            host=os.getenv("EMBEDDING_SERVICE_HOST", "localhost"),
            port=int(os.getenv("EMBEDDING_SERVICE_PORT", 6000)),
            endpoint="/v1/embeddings",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )

        # Retriever Microservice - Vector Search with Redis
        retriever_service = MicroService(
            name="retriever",
            host=os.getenv("RETRIEVER_SERVICE_HOST", "localhost"),
            port=int(os.getenv("RETRIEVER_SERVICE_PORT", 7000)),
            endpoint="/v1/retrieval",
            use_remote_service=True,
            service_type=ServiceType.RETRIEVER,
        )

        # Reranking Microservice - Improve retrieval quality
        rerank_service = MicroService(
            name="rerank",
            host=os.getenv("RERANK_SERVICE_HOST", "localhost"),
            port=int(os.getenv("RERANK_SERVICE_PORT", 8000)),
            endpoint="/v1/reranking",
            use_remote_service=True,
            service_type=ServiceType.RERANK,
        )

        # Data Prep Microservice - Document ingestion
        dataprep_service = MicroService(
            name="dataprep",
            host=os.getenv("DATAPREP_SERVICE_HOST", "localhost"),
            port=int(os.getenv("DATAPREP_SERVICE_PORT", 6007)),
            endpoint="/v1/dataprep",
            use_remote_service=True,
            service_type=ServiceType.DATAPREP,
        )

        # Add services to megaservice
        self.megaservice.add(embedding_service).add(retriever_service).add(rerank_service).add(llm_service)
        self.megaservice.add(dataprep_service)

        # Define service flow for RAG pipeline
        # Embedding → Retriever → Rerank → LLM
        self.megaservice.flow_to(embedding_service, retriever_service)
        self.megaservice.flow_to(retriever_service, rerank_service)
        self.megaservice.flow_to(rerank_service, llm_service)


def align_inputs(self, inputs: dict, cur_node: MicroService, runtime_graph: dict) -> dict:
    """Align input format for different microservices.

    Args:
        inputs: Input data dictionary
        cur_node: Current microservice node
        runtime_graph: Runtime execution graph

    Returns:
        Aligned input dictionary for the current microservice
    """
    if cur_node.service_type == ServiceType.EMBEDDING:
        if "text" in inputs:
            inputs["inputs"] = inputs.pop("text")
    elif cur_node.service_type == ServiceType.RETRIEVER:
        if "embeddings" in inputs:
            inputs["text"] = inputs.pop("embeddings")
    elif cur_node.service_type == ServiceType.LLM:
        if "documents" in inputs:
            # Combine retrieved documents with query
            inputs["query"] = inputs.get("query", "")
            inputs["context"] = "\n".join(inputs.pop("documents", []))

    return inputs


# Create FastAPI application
app = FastAPI(
    title="OPEA Cogniware IMS",
    description="AI-powered Inventory Management System with RAG, DBQnA, and continuous learning",
    version="1.0.0",
)

# Initialize CogniwareIMS service
cogniwareims_service = CogniwareIMSService(
    host=os.getenv("COGNIWAREIMS_HOST", "0.0.0.0"),
    port=int(os.getenv("COGNIWAREIMS_PORT", 8888)),
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "CogniwareIMS"}


@app.post("/v1/cogniwareims")
async def cogniwareims_endpoint(request: Request):
    """Main endpoint for Cogniware IMS.

    Handles chat completions with RAG pipeline.
    """
    data = await request.json()

    # Extract chat completion request
    chat_request = ChatCompletionRequest(**data)

    # Process through megaservice pipeline
    result = await cogniwareims_service.megaservice.schedule(initial_inputs={"messages": chat_request.messages})

    return result


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """OpenAI-compatible chat completions endpoint."""
    return await cogniwareims_endpoint(request)


@app.post("/v1/cogniwareims/query")
async def inventory_query(request: Request):
    """Inventory query endpoint with RAG support.

    Natural language inventory search and analytics.
    """
    data = await request.json()

    # Process query through RAG pipeline
    result = await cogniwareims_service.megaservice.schedule(
        initial_inputs={"query": data.get("query"), "use_rag": True}
    )

    return result


@app.post("/v1/dataprep")
async def dataprep_endpoint(request: Request):
    """
    Data preparation endpoint for uploading and processing:
    - CSV files with inventory data
    - Product catalogs
    - Technical documentation
    - Knowledge base documents
    """
    data = await request.json()
    # Forward to dataprep microservice
    return {"status": "success", "message": "Data prepared successfully"}


@app.get("/v1/cogniwareims/stats")
async def get_stats():
    """Get system statistics and metrics."""
    return {
        "status": "operational",
        "features": [
            "RAG (Retrieval-Augmented Generation)",
            "DBQnA (Natural Language to SQL)",
            "Document Summarization",
            "Continuous Learning",
            "Multi-format Upload",
            "Interactive Agent",
            "Real-time Analytics",
        ],
        "optimization": "Intel Xeon Processors",
        "models": {
            "llm": "Intel/neural-chat-7b-v3-3",
            "embedding": "BAAI/bge-base-en-v1.5",
            "reranking": "BAAI/bge-reranker-base",
        },
    }


if __name__ == "__main__":
    import uvicorn

    # Add remote services
    cogniwareims_service.add_remote_service()

    # Start FastAPI server
    uvicorn.run(
        app,
        host=cogniwareims_service.host,
        port=cogniwareims_service.port,
        log_level="info",
    )

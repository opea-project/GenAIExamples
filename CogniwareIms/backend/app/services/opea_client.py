# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""OPEA Microservices Client Handles communication with OPEA GenAIComps microservices."""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class OPEAClient:
    """Client for OPEA GenAIComps microservices."""

    def __init__(self):
        self.embedding_url = os.getenv("OPEA_EMBEDDING_URL", "http://localhost:6000")
        self.retrieval_url = os.getenv("OPEA_RETRIEVAL_URL", "http://localhost:7000")
        self.llm_url = os.getenv("OPEA_LLM_URL", "http://localhost:9000")
        self.dbqna_url = os.getenv("OPEA_DBQNA_URL", "http://localhost:8888")
        self.timeout = httpx.Timeout(60.0, connect=10.0)

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using OPEA embedding service."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.embedding_url}/v1/embeddings", json={"text": text})
                response.raise_for_status()
                result = response.json()
                return result.get("embedding", [])
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Embedding service error: {str(e)}")

    async def query_with_rag(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Query using Retrieval-Augmented Generation."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {"question": query, "context": context or ""}
                response = await client.post(f"{self.llm_url}/v1/chat/completions", json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            raise HTTPException(status_code=500, detail=f"LLM service error: {str(e)}")

    async def query_database(self, question: str, database_schema: Optional[Dict] = None) -> Dict[str, Any]:
        """Query database using OPEA DBQnA agent."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {"question": question, "schema": database_schema or {}}
                response = await client.post(f"{self.dbqna_url}/v1/query", json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            # Return mock data if service is unavailable
            return self._get_mock_query_result(question)

    async def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search using OPEA retrieval service."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.retrieval_url}/v1/search",
                    json={"query": query, "top_k": top_k},
                )
                response.raise_for_status()
                return response.json().get("results", [])
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    async def summarize_document(self, text: str) -> str:
        """Summarize document using OPEA DocSummarization agent."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.llm_url}/v1/summarize", json={"text": text})
                response.raise_for_status()
                result = response.json()
                return result.get("summary", "")
        except Exception as e:
            logger.error(f"Document summarization failed: {e}")
            return text[:200] + "..."  # Fallback to truncation

    def _get_mock_query_result(self, question: str) -> Dict[str, Any]:
        """Get mock query result when OPEA services are unavailable."""
        if "xeon 6" in question.lower():
            return {
                "result": {
                    "product": "Intel Xeon 6 Processor",
                    "sku": "CPU-XN6-2024",
                    "location": "San Jose Warehouse",
                    "available": 247,
                    "reserved": 32,
                    "in_transit": 15,
                }
            }
        return {"result": {"message": "No results found"}}

    async def health_check_all(self) -> Dict[str, str]:
        """Check health of all OPEA microservices."""
        services = {
            "embedding": self.embedding_url,
            "retrieval": self.retrieval_url,
            "llm": self.llm_url,
            "dbqna": self.dbqna_url,
        }

        status = {}
        for name, url in services.items():
            status[name] = await self._check_service(url)

        return status

    async def _check_service(self, url: str) -> str:
        """Check if a service is healthy."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    return "healthy"
                else:
                    return f"unhealthy (status: {response.status_code})"
        except Exception as e:
            logger.error(f"Health check failed for {url}: {e}")
            return f"unhealthy (error: {str(e)})"


# Global OPEA client instance
opea_client = OPEAClient()

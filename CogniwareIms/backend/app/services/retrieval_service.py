# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""OPEA Retrieval Service Integration Handles semantic search and document retrieval using Redis vector store."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
import numpy as np
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RetrievalService:
    """Integration with OPEA Retrieval microservice and Redis vector store."""

    def __init__(self):
        self.base_url = os.getenv("OPEA_RETRIEVAL_URL", "http://retrieval-service:7000")
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        self.redis_client = None

    async def get_redis_client(self):
        """Get or create Redis client."""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(self.redis_url, encoding="utf-8", decode_responses=False)
        return self.redis_client

    async def index_document(self, doc_id: str, text: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Index a document in the vector store."""
        try:
            # Store in Redis
            client = await self.get_redis_client()

            doc_data = {
                "id": doc_id,
                "text": text,
                "embedding": embedding,
                "metadata": metadata,
            }

            # Store document
            await client.set(f"doc:{doc_id}", json.dumps(doc_data))

            # Store embedding separately for vector search
            embedding_key = f"embedding:{doc_id}"
            await client.set(embedding_key, json.dumps(embedding))

            # Add to index
            await client.sadd("document_ids", doc_id)

            logger.info(f"Indexed document: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Error indexing document {doc_id}: {e}")
            return False

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic search using query embedding."""
        try:
            # Try OPEA retrieval service first
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/search",
                    json={
                        "embedding": query_embedding,
                        "top_k": top_k,
                        "filters": filters or {},
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("results", [])

        except Exception as e:
            logger.warning(f"OPEA retrieval service unavailable, using direct Redis: {e}")

        # Fallback to direct Redis search
        return await self._redis_search(query_embedding, top_k, filters)

    async def _redis_search(
        self, query_embedding: List[float], top_k: int, filters: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """Direct Redis vector similarity search."""
        try:
            client = await self.get_redis_client()

            # Get all document IDs
            doc_ids = await client.smembers("document_ids")

            # Calculate similarities
            similarities = []
            query_vec = np.array(query_embedding)

            for doc_id in doc_ids:
                # Get document
                doc_json = await client.get(f"doc:{doc_id.decode() if isinstance(doc_id, bytes) else doc_id}")
                if doc_json:
                    doc = json.loads(doc_json)
                    doc_embedding = np.array(doc.get("embedding", []))

                    # Calculate cosine similarity
                    if len(doc_embedding) > 0:
                        similarity = np.dot(query_vec, doc_embedding) / (
                            np.linalg.norm(query_vec) * np.linalg.norm(doc_embedding)
                        )

                        # Apply filters if any
                        if filters:
                            metadata = doc.get("metadata", {})
                            if all(metadata.get(k) == v for k, v in filters.items()):
                                similarities.append(
                                    {
                                        "doc_id": doc["id"],
                                        "text": doc["text"],
                                        "metadata": metadata,
                                        "score": float(similarity),
                                    }
                                )
                        else:
                            similarities.append(
                                {
                                    "doc_id": doc["id"],
                                    "text": doc["text"],
                                    "metadata": doc.get("metadata", {}),
                                    "score": float(similarity),
                                }
                            )

            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x["score"], reverse=True)
            return similarities[:top_k]

        except Exception as e:
            logger.error(f"Redis search error: {e}")
            return []

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the vector store."""
        try:
            client = await self.get_redis_client()

            await client.delete(f"doc:{doc_id}")
            await client.delete(f"embedding:{doc_id}")
            await client.srem("document_ids", doc_id)

            logger.info(f"Deleted document: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False

    async def update_document(self, doc_id: str, text: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Update an existing document."""
        # Delete old version
        await self.delete_document(doc_id)

        # Index new version
        return await self.index_document(doc_id, text, embedding, metadata)

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific document by ID."""
        try:
            client = await self.get_redis_client()
            doc_json = await client.get(f"doc:{doc_id}")

            if doc_json:
                return json.loads(doc_json)
            return None

        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {e}")
            return None

    async def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all indexed documents."""
        try:
            client = await self.get_redis_client()
            doc_ids = await client.smembers("document_ids")

            documents = []
            for i, doc_id in enumerate(list(doc_ids)[offset : offset + limit]):
                doc = await self.get_document(doc_id.decode() if isinstance(doc_id, bytes) else doc_id)
                if doc:
                    documents.append(doc)

            return documents

        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []

    async def count_documents(self) -> int:
        """Get total number of indexed documents."""
        try:
            client = await self.get_redis_client()
            count = await client.scard("document_ids")
            return count
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0

    async def clear_all_documents(self) -> bool:
        """Clear entire vector store (use with caution)"""
        try:
            client = await self.get_redis_client()
            doc_ids = await client.smembers("document_ids")

            for doc_id in doc_ids:
                await self.delete_document(doc_id.decode() if isinstance(doc_id, bytes) else doc_id)

            logger.warning("Cleared all documents from vector store")
            return True

        except Exception as e:
            logger.error(f"Error clearing documents: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check health of retrieval service and Redis."""
        status = {"opea_service": False, "redis": False, "document_count": 0}

        # Check OPEA service
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(f"{self.base_url}/v1/health_check")
                status["opea_service"] = response.status_code == 200
        except:
            pass

        # Check Redis
        try:
            client = await self.get_redis_client()
            await client.ping()
            status["redis"] = True
            status["document_count"] = await self.count_documents()
        except:
            pass

        return status


# Global instance
retrieval_service = RetrievalService()

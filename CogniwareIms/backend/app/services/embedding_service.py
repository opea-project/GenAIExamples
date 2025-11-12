# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""OPEA Embedding Service Integration Handles text vectorization and embedding generation."""

import logging
import os
from functools import lru_cache
from typing import Any, Dict, List

import httpx
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Integration with OPEA Embedding microservice."""

    def __init__(self):
        self.base_url = os.getenv("OPEA_EMBEDDING_URL", "http://embedding-service:6000")
        self.model_id = os.getenv("EMBEDDING_MODEL_ID", "BAAI/bge-base-en-v1.5")
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        self.cache = {}

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text Uses OPEA embedding microservice."""
        # Check cache first
        if text in self.cache:
            logger.debug(f"Cache hit for text: {text[:50]}...")
            return self.cache[text]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/embeddings",
                    json={"input": text, "model": self.model_id},
                )
                response.raise_for_status()
                result = response.json()

                # Extract embedding from response
                if "data" in result and len(result["data"]) > 0:
                    embedding = result["data"][0]["embedding"]
                elif "embedding" in result:
                    embedding = result["embedding"]
                else:
                    raise ValueError("Invalid embedding response format")

                # Cache the result
                self.cache[text] = embedding
                logger.info(f"Generated embedding for text: {text[:50]}...")

                return embedding

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling embedding service: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches More efficient for large datasets."""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/v1/embeddings",
                        json={"input": batch, "model": self.model_id},
                    )
                    response.raise_for_status()
                    result = response.json()

                    # Extract embeddings
                    if "data" in result:
                        batch_embeddings = [item["embedding"] for item in result["data"]]
                    else:
                        # Fallback: generate one by one
                        batch_embeddings = []
                        for text in batch:
                            emb = await self.embed_text(text)
                            batch_embeddings.append(emb)

                    embeddings.extend(batch_embeddings)
                    logger.info(f"Generated {len(batch_embeddings)} embeddings")

            except Exception as e:
                logger.error(f"Batch embedding failed for batch {i//batch_size}: {e}")
                # Try individual embeddings as fallback
                for text in batch:
                    try:
                        emb = await self.embed_text(text)
                        embeddings.append(emb)
                    except:
                        embeddings.append([0.0] * 768)  # Zero vector as last resort

        return embeddings

    async def embed_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Embed a list of documents with metadata Returns documents with added embedding field."""
        texts = [doc.get("text", "") for doc in documents]
        embeddings = await self.embed_batch(texts)

        # Add embeddings to documents
        embedded_docs = []
        for doc, embedding in zip(documents, embeddings):
            embedded_doc = doc.copy()
            embedded_doc["embedding"] = embedding
            embedded_docs.append(embedded_doc)

        logger.info(f"Embedded {len(embedded_docs)} documents")
        return embedded_docs

    @lru_cache(maxsize=1000)
    def cosine_similarity(self, vec1_tuple: tuple, vec2_tuple: tuple) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1_tuple)
        vec2 = np.array(vec2_tuple)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    async def find_similar(self, query_text: str, candidate_texts: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """Find most similar texts to query using cosine similarity."""
        # Generate query embedding
        query_embedding = await self.embed_text(query_text)

        # Generate candidate embeddings
        candidate_embeddings = await self.embed_batch(candidate_texts)

        # Calculate similarities
        similarities = []
        for idx, (text, embedding) in enumerate(zip(candidate_texts, candidate_embeddings)):
            similarity = self.cosine_similarity(tuple(query_embedding), tuple(embedding))
            similarities.append({"text": text, "index": idx, "similarity": similarity})

        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:top_k]

    async def health_check(self) -> bool:
        """Check if embedding service is available."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(f"{self.base_url}/v1/health_check")
                return response.status_code == 200
        except:
            return False


# Global instance
embedding_service = EmbeddingService()

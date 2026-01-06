# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Knowledge Base Manager Handles continuous learning and knowledge base updates Allows users to add new knowledge and
retrain on combined old+new data."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .embedding_service import embedding_service
from .retrieval_service import retrieval_service

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """Manages knowledge base with continuous learning capabilities Users can add new documents/data and system retrains
    automatically."""

    def __init__(self, data_dir: str = "../data"):
        self.data_dir = Path(data_dir)
        self.knowledge_dir = self.data_dir / "knowledge_base"
        self.knowledge_dir.mkdir(exist_ok=True, parents=True)

        self.history_file = self.knowledge_dir / "training_history.json"
        self.load_history()

    def load_history(self):
        """Load training history."""
        if self.history_file.exists():
            with open(self.history_file, "r") as f:
                self.history = json.load(f)
        else:
            self.history = {
                "training_runs": [],
                "total_documents": 0,
                "last_update": None,
            }

    def save_history(self):
        """Save training history."""
        with open(self.history_file, "w") as f:
            json.dump(self.history, f, indent=2)

    async def add_knowledge_from_text(
        self,
        text: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
        auto_train: bool = True,
    ) -> Dict[str, Any]:
        """Add new knowledge from text input.

        Args:
            text: The knowledge text to add
            source: Source identifier (e.g., "user_input", "csv_import")
            metadata: Additional metadata
            auto_train: Automatically retrain/re-embed after adding

        Returns:
            Status dict with document ID and training info
        """
        try:
            # Generate unique document ID
            doc_id = f"{source}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

            # Prepare metadata
            full_metadata = {
                "source": source,
                "added_at": datetime.now().isoformat(),
                "added_by": metadata.get("user", "system") if metadata else "system",
                **(metadata or {}),
            }

            # Generate embedding
            embedding = await embedding_service.embed_text(text)

            # Index in vector store
            success = await retrieval_service.index_document(
                doc_id=doc_id, text=text, embedding=embedding, metadata=full_metadata
            )

            if success:
                # Update history
                self.history["total_documents"] += 1
                self.history["last_update"] = datetime.now().isoformat()
                self.save_history()

                logger.info(f"Added knowledge document: {doc_id}")

                return {
                    "success": True,
                    "doc_id": doc_id,
                    "message": "Knowledge added successfully",
                    "total_documents": self.history["total_documents"],
                }
            else:
                raise Exception("Failed to index document")

        except Exception as e:
            logger.error(f"Error adding knowledge: {e}")
            return {"success": False, "error": str(e)}

    async def add_knowledge_from_csv(self, csv_file: Path, auto_train: bool = True) -> Dict[str, Any]:
        """Add knowledge from CSV file Each row becomes a document in the knowledge base."""
        try:
            df = pd.read_csv(csv_file)
            added_count = 0

            for idx, row in df.iterrows():
                # Create text representation
                text_parts = [f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])]
                text = " | ".join(text_parts)

                # Add to knowledge base
                result = await self.add_knowledge_from_text(
                    text=text,
                    source=f"csv_{csv_file.stem}",
                    metadata={
                        "file": csv_file.name,
                        "row_index": idx,
                        "raw_data": row.to_dict(),
                    },
                    auto_train=False,  # Batch training at end
                )

                if result["success"]:
                    added_count += 1

            # Record training run
            self.history["training_runs"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "source": f"csv_{csv_file.name}",
                    "documents_added": added_count,
                    "total_documents": self.history["total_documents"],
                }
            )
            self.save_history()

            logger.info(f"Added {added_count} documents from CSV: {csv_file.name}")

            return {
                "success": True,
                "documents_added": added_count,
                "total_documents": self.history["total_documents"],
                "file": csv_file.name,
            }

        except Exception as e:
            logger.error(f"Error processing CSV: {e}")
            return {"success": False, "error": str(e)}

    async def add_knowledge_batch(
        self, documents: List[Dict[str, str]], source: str = "batch_import"
    ) -> Dict[str, Any]:
        """Add multiple documents at once.

        Args:
            documents: List of {"text": "...", "metadata": {...}}
            source: Source identifier
        """
        added_count = 0
        failed_count = 0

        # Generate embeddings in batch (more efficient)
        texts = [doc["text"] for doc in documents]
        embeddings = await embedding_service.embed_batch(texts)

        # Index all documents
        for doc, embedding in zip(documents, embeddings):
            doc_id = f"{source}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{added_count}"

            success = await retrieval_service.index_document(
                doc_id=doc_id,
                text=doc["text"],
                embedding=embedding,
                metadata={
                    "source": source,
                    "added_at": datetime.now().isoformat(),
                    **doc.get("metadata", {}),
                },
            )

            if success:
                added_count += 1
            else:
                failed_count += 1

        # Update history
        self.history["total_documents"] += added_count
        self.history["last_update"] = datetime.now().isoformat()
        self.history["training_runs"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "source": source,
                "documents_added": added_count,
                "documents_failed": failed_count,
                "total_documents": self.history["total_documents"],
            }
        )
        self.save_history()

        logger.info(f"Batch import: {added_count} added, {failed_count} failed")

        return {
            "success": True,
            "added": added_count,
            "failed": failed_count,
            "total_documents": self.history["total_documents"],
        }

    async def update_knowledge(
        self, doc_id: str, new_text: str, new_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update existing knowledge document Regenerates embedding and updates index."""
        try:
            # Get existing document
            existing = await retrieval_service.get_document(doc_id)
            if not existing:
                return {"success": False, "error": "Document not found"}

            # Merge metadata
            metadata = existing.get("metadata", {})
            if new_metadata:
                metadata.update(new_metadata)
            metadata["updated_at"] = datetime.now().isoformat()

            # Generate new embedding
            embedding = await embedding_service.embed_text(new_text)

            # Update in vector store
            success = await retrieval_service.update_document(
                doc_id=doc_id, text=new_text, embedding=embedding, metadata=metadata
            )

            if success:
                logger.info(f"Updated knowledge document: {doc_id}")
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "message": "Knowledge updated successfully",
                }
            else:
                raise Exception("Failed to update document")

        except Exception as e:
            logger.error(f"Error updating knowledge: {e}")
            return {"success": False, "error": str(e)}

    async def delete_knowledge(self, doc_id: str) -> Dict[str, Any]:
        """Delete a knowledge document."""
        try:
            success = await retrieval_service.delete_document(doc_id)

            if success:
                self.history["total_documents"] -= 1
                self.save_history()

                return {"success": True, "message": "Knowledge deleted successfully"}
            else:
                raise Exception("Failed to delete document")

        except Exception as e:
            logger.error(f"Error deleting knowledge: {e}")
            return {"success": False, "error": str(e)}

    async def search_knowledge(
        self, query: str, top_k: int = 5, filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search knowledge base using semantic search."""
        try:
            # Generate query embedding
            query_embedding = await embedding_service.embed_text(query)

            # Search vector store
            results = await retrieval_service.search(query_embedding=query_embedding, top_k=top_k, filters=filters)

            return results

        except Exception as e:
            logger.error(f"Knowledge search error: {e}")
            return []

    async def retrain_all(self) -> Dict[str, Any]:
        """Retrain entire knowledge base Useful after bulk updates or schema changes."""
        try:
            logger.info("Starting full knowledge base retraining...")

            # Get all existing documents
            documents = await retrieval_service.get_all_documents(limit=10000)

            if not documents:
                return {"success": False, "error": "No documents to retrain"}

            # Re-embed all documents
            texts = [doc["text"] for doc in documents]
            new_embeddings = await embedding_service.embed_batch(texts)

            # Reindex all documents
            success_count = 0
            for doc, new_embedding in zip(documents, new_embeddings):
                success = await retrieval_service.update_document(
                    doc_id=doc["id"],
                    text=doc["text"],
                    embedding=new_embedding,
                    metadata=doc.get("metadata", {}),
                )
                if success:
                    success_count += 1

            # Record retraining
            self.history["training_runs"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "full_retrain",
                    "documents_processed": success_count,
                    "total_documents": self.history["total_documents"],
                }
            )
            self.save_history()

            logger.info(f"Retraining complete: {success_count}/{len(documents)} documents")

            return {
                "success": True,
                "documents_retrained": success_count,
                "total_documents": len(documents),
            }

        except Exception as e:
            logger.error(f"Retraining error: {e}")
            return {"success": False, "error": str(e)}

    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        try:
            total_docs = await retrieval_service.count_documents()

            return {
                "total_documents": total_docs,
                "last_update": self.history.get("last_update"),
                "training_runs": len(self.history.get("training_runs", [])),
                "recent_runs": self.history.get("training_runs", [])[-5:],  # Last 5 runs
                "storage": {"vector_store": "Redis", "indexed": total_docs},
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}

    async def export_knowledge_base(self, output_file: Optional[Path] = None) -> Path:
        """Export entire knowledge base to JSON file."""
        try:
            documents = await retrieval_service.get_all_documents(limit=100000)

            export_data = {
                "exported_at": datetime.now().isoformat(),
                "total_documents": len(documents),
                "documents": documents,
                "history": self.history,
            }

            if not output_file:
                output_file = self.knowledge_dir / f"export_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"

            with open(output_file, "w") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Exported knowledge base to: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Export error: {e}")
            raise

    async def import_knowledge_base(self, import_file: Path) -> Dict[str, Any]:
        """Import knowledge base from JSON file."""
        try:
            with open(import_file, "r") as f:
                import_data = json.load(f)

            documents = import_data.get("documents", [])

            # Add all documents
            result = await self.add_knowledge_batch(
                documents=[{"text": doc["text"], "metadata": doc.get("metadata", {})} for doc in documents],
                source=f"import_{import_file.stem}",
            )

            logger.info(f"Imported {result['added']} documents from: {import_file}")
            return result

        except Exception as e:
            logger.error(f"Import error: {e}")
            return {"success": False, "error": str(e)}


# Global instance
knowledge_manager = KnowledgeManager(data_dir=os.getenv("CSV_DATA_DIR", "../data"))

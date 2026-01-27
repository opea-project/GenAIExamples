# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Knowledge Base Initialization Script Processes all CSV files and creates initial embeddings Run this after first
deployment to populate the knowledge base."""

import asyncio
import logging
import sys
from pathlib import Path

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.csv_processor import csv_processor
from app.services.embedding_service import embedding_service
from app.services.knowledge_manager import knowledge_manager
from app.services.retrieval_service import retrieval_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def initialize_knowledge_base():
    """Initialize complete knowledge base from CSV data."""
    logger.info("=" * 60)
    logger.info("🚀 Starting Knowledge Base Initialization")
    logger.info("=" * 60)

    try:
        # Step 1: Load all CSV files
        logger.info("\n📁 Step 1: Loading CSV files...")
        dataframes = csv_processor.load_all_csv_files()
        logger.info(f"   Loaded {len(dataframes)} CSV files")

        # Step 2: Prepare documents for embedding
        logger.info("\n📄 Step 2: Preparing documents...")
        documents = csv_processor.prepare_for_embedding(dataframes)
        logger.info(f"   Prepared {len(documents)} documents")

        # Step 3: Process in batches
        logger.info("\n🔄 Step 3: Generating embeddings and indexing...")
        batch_size = 50
        total_indexed = 0

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            logger.info(f"   Processing batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}...")

            # Extract texts
            texts = [doc["text"] for doc in batch]

            # Generate embeddings in batch
            embeddings = await embedding_service.embed_batch(texts, batch_size=batch_size)

            # Index each document
            for doc, embedding in zip(batch, embeddings):
                success = await retrieval_service.index_document(
                    doc_id=doc["id"],
                    text=doc["text"],
                    embedding=embedding,
                    metadata=doc.get("metadata", {}),
                )

                if success:
                    total_indexed += 1

            logger.info(f"   Indexed {total_indexed}/{len(documents)} documents")

        # Step 4: Update knowledge manager history
        logger.info("\n📊 Step 4: Updating knowledge base statistics...")
        knowledge_manager.history["total_documents"] = total_indexed
        knowledge_manager.history["last_update"] = pd.Timestamp.now().isoformat()
        knowledge_manager.history["training_runs"].append(
            {
                "timestamp": pd.Timestamp.now().isoformat(),
                "type": "initial_setup",
                "documents_added": total_indexed,
                "source": "csv_bulk_import",
            }
        )
        knowledge_manager.save_history()

        # Step 5: Verify
        logger.info("\n✅ Step 5: Verification...")
        doc_count = await retrieval_service.count_documents()
        logger.info(f"   Vector store contains {doc_count} documents")

        logger.info("\n" + "=" * 60)
        logger.info("🎉 Knowledge Base Initialization Complete!")
        logger.info("=" * 60)
        logger.info("\n📊 Summary:")
        logger.info(f"   CSV Files Processed: {len(dataframes)}")
        logger.info(f"   Documents Indexed: {total_indexed}")
        logger.info(f"   Vector Store Count: {doc_count}")
        logger.info("\n✅ System is ready for AI-powered queries!")

        return {
            "success": True,
            "csv_files": len(dataframes),
            "documents_indexed": total_indexed,
            "vector_store_count": doc_count,
        }

    except Exception as e:
        logger.error(f"\n❌ Initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def quick_test():
    """Quick test of knowledge base functionality."""
    logger.info("\n🧪 Running Quick Test...")

    try:
        # Test embedding
        test_text = "Intel Xeon 6 Processor"
        embedding = await embedding_service.embed_text(test_text)
        logger.info(f"✅ Embedding generation: OK (dimension: {len(embedding)})")

        # Test search
        results = await retrieval_service.search(embedding, top_k=3)
        logger.info(f"✅ Vector search: OK (found {len(results)} results)")

        # Test knowledge manager
        stats = await knowledge_manager.get_knowledge_stats()
        logger.info(f"✅ Knowledge manager: OK ({stats.get('total_documents', 0)} documents)")

        logger.info("\n🎉 All systems operational!")

    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    # Check if test mode
    test_mode = "--test" in sys.argv

    if test_mode:
        asyncio.run(quick_test())
    else:
        result = asyncio.run(initialize_knowledge_base())

        if result["success"]:
            # Run quick test after initialization
            asyncio.run(quick_test())
            sys.exit(0)
        else:
            sys.exit(1)

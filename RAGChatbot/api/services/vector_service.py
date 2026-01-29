"""
Vector store service
Handles FAISS vector store operations
"""

import os
import logging
import shutil
from typing import Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
import config

logger = logging.getLogger(__name__)

# Constants
VECTOR_STORE_PATH = "./dmv_index"


class CustomEmbeddings(Embeddings):
    """
    Custom embeddings class that uses the bge-base-en-v1.5 endpoint
    """
    
    def __init__(self):
        from .api_client import get_api_client
        self.api_client = get_api_client()
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple documents
        Note: Batches are handled automatically by api_client (max batch size: 32)
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        return self.api_client.embed_texts(texts)
    
    def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return self.api_client.embed_text(text)


def get_embeddings(api_key: str) -> Embeddings:
    """
    Create embeddings instance

    Args:
        api_key: API key (for compatibility, not used with custom endpoint)

    Returns:
        Embeddings instance (CustomEmbeddings if using custom API, OpenAIEmbeddings otherwise)
    """
    # Check if using custom inference endpoint
    if hasattr(config, 'INFERENCE_API_TOKEN') and config.INFERENCE_API_TOKEN:
        return CustomEmbeddings()
    else:
        # Fallback to OpenAI
        return OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=api_key
        )


def store_in_vector_storage(chunks: list, api_key: str) -> FAISS:
    """
    Create embeddings and store in FAISS vector store
    
    Args:
        chunks: List of document chunks
        api_key: OpenAI API key
        
    Returns:
        FAISS vectorstore instance
        
    Raises:
        Exception: If storage operation fails
    """
    try:
        embeddings = get_embeddings(api_key)
        vectorstore = FAISS.from_documents(chunks, embeddings)
        
        # Ensure directory exists
        os.makedirs(
            os.path.dirname(VECTOR_STORE_PATH) if os.path.dirname(VECTOR_STORE_PATH) else ".",
            exist_ok=True
        )
        vectorstore.save_local(VECTOR_STORE_PATH)
        logger.info(f"Saved vector store to {VECTOR_STORE_PATH}")
        
        return vectorstore
    except Exception as e:
        logger.error(f"Error storing vectors: {str(e)}")
        raise


def load_vector_store(api_key: str) -> Optional[FAISS]:
    """
    Load existing FAISS vector store
    
    Args:
        api_key: OpenAI API key
        
    Returns:
        FAISS vectorstore instance or None if not found
    """
    try:
        embeddings = get_embeddings(api_key)
        vectorstore = FAISS.load_local(
            VECTOR_STORE_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        logger.info("Loaded existing FAISS vector store")
        return vectorstore
    except Exception as e:
        logger.warning(f"Could not load vector store: {str(e)}")
        return None


def delete_vector_store() -> bool:
    """
    Delete the vector store from disk
    
    Returns:
        True if deleted successfully, False otherwise
        
    Raises:
        Exception: If deletion fails
    """
    try:
        if os.path.exists(VECTOR_STORE_PATH):
            shutil.rmtree(VECTOR_STORE_PATH)
            logger.info("Deleted vector store")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting vector store: {str(e)}")
        raise


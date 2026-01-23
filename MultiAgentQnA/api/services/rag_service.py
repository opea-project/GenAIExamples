"""
RAG Service for PDF processing and vector store management
Handles PDF parsing, text chunking, and FAISS vector operations
"""

import os
import logging
import shutil
from typing import List, Optional, Dict, Any
import numpy as np
import faiss
from pypdf import PdfReader
import config
from services.api_client import get_api_client

logger = logging.getLogger(__name__)

# Constants
VECTOR_STORE_DIR = "./rag_index"
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks


class RAGService:
    """
    Service for RAG operations: PDF processing, embedding, and retrieval
    """
    
    def __init__(self):
        self.api_client = get_api_client()
        self.vector_store_path = VECTOR_STORE_DIR
        self.index: Optional[faiss.Index] = None
        self.documents: List[Dict[str, Any]] = []
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure the vector store directory exists"""
        os.makedirs(self.vector_store_path, exist_ok=True)
    
    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Process a PDF file and extract text chunks
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of document chunks with metadata
        """
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            reader = PdfReader(pdf_path)
            
            # Extract text from all pages
            full_text = ""
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    full_text += f"\n--- Page {i+1} ---\n{page_text}\n"
            
            if not full_text.strip():
                raise ValueError("No text extracted from PDF")
            
            # Chunk the text
            chunks = self._chunk_text(full_text, metadata={"source": pdf_path})
            
            logger.info(f"Extracted {len(chunks)} chunks from PDF")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise
    
    def _chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            metadata: Metadata to attach to chunks
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            # If adding this paragraph would exceed chunk size, save current chunk
            if current_size + para_size > CHUNK_SIZE and current_chunk:
                chunks.append({
                    "text": current_chunk,
                    "metadata": {**metadata, "chunk_index": len(chunks)}
                })
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-CHUNK_OVERLAP:] if len(current_chunk) > CHUNK_OVERLAP else current_chunk
                current_chunk = overlap_text + " " + para
                current_size = len(current_chunk)
            else:
                current_chunk += "\n\n" + para if current_chunk else para
                current_size = len(current_chunk)
        
        # Add the last chunk
        if current_chunk:
            chunks.append({
                "text": current_chunk,
                "metadata": {**metadata, "chunk_index": len(chunks)}
            })
        
        return chunks
    
    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Create embeddings and build FAISS index
        
        Args:
            chunks: List of document chunks
        """
        try:
            logger.info(f"Building FAISS index with {len(chunks)} chunks")
            
            # Extract texts
            texts = [chunk["text"] for chunk in chunks]
            
            # Get embeddings from API
            embeddings = self.api_client.embed_texts(texts)
            
            # Convert to numpy array
            embedding_dim = len(embeddings[0])
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Create FAISS index (using L2 distance)
            self.index = faiss.IndexFlatL2(embedding_dim)
            self.index.add(embeddings_array)
            
            # Store documents
            self.documents = chunks
            
            # Save to disk
            self._save_index()
            
            logger.info(f"Index built successfully with {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Error building index: {str(e)}")
            raise
    
    def _save_index(self):
        """Save FAISS index and documents to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, os.path.join(self.vector_store_path, "index.faiss"))
            
            # Save documents as a simple format (JSON would be better but keeping it simple)
            import pickle
            with open(os.path.join(self.vector_store_path, "documents.pkl"), "wb") as f:
                pickle.dump(self.documents, f)
            
            logger.info(f"Index saved to {self.vector_store_path}")
            
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            raise
    
    def load_index(self) -> bool:
        """
        Load FAISS index from disk
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            faiss_path = os.path.join(self.vector_store_path, "index.faiss")
            docs_path = os.path.join(self.vector_store_path, "documents.pkl")
            
            if not os.path.exists(faiss_path) or not os.path.exists(docs_path):
                logger.warning("No existing index found")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(faiss_path)
            
            # Load documents
            import pickle
            with open(docs_path, "rb") as f:
                self.documents = pickle.load(f)
            
            logger.info(f"Loaded index with {self.index.ntotal} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            return False
    
    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of matching documents with similarity scores
        """
        try:
            if not self.index or self.index.ntotal == 0:
                logger.warning("No index loaded or index is empty")
                return []
            
            # Get query embedding
            query_embedding = self.api_client.embed_text(query)
            query_vector = np.array([query_embedding], dtype=np.float32)
            
            # Search
            distances, indices = self.index.search(query_vector, k)
            
            # Retrieve documents
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    results.append({
                        "document": self.documents[idx],
                        "score": float(distances[0][i]),
                        "similarity": 1.0 / (1.0 + float(distances[0][i]))  # Convert distance to similarity
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            raise
    
    def delete_index(self) -> bool:
        """
        Delete the vector store
        
        Returns:
            True if deleted successfully
        """
        try:
            if os.path.exists(self.vector_store_path):
                shutil.rmtree(self.vector_store_path)
                logger.info("Vector store deleted")
                self.index = None
                self.documents = []
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting vector store: {str(e)}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the vector store
        
        Returns:
            Dictionary with status information
        """
        return {
            "index_exists": self.index is not None,
            "num_documents": self.index.ntotal if self.index else 0,
            "num_vectors": self.index.ntotal if self.index else 0,
            "path": self.vector_store_path
        }


# Global RAG service instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Get or create the global RAG service instance
    
    Returns:
        RAGService instance
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
        # Try to load existing index
        _rag_service.load_index()
    return _rag_service


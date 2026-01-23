"""
PDF processing service
Handles PDF validation, loading, and text splitting
"""

import logging
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Constants
ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def validate_pdf_file(file: UploadFile) -> None:
    """
    Validate uploaded PDF file
    
    Args:
        file: UploadFile object from FastAPI
        
    Raises:
        HTTPException: If file validation fails
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only PDF files are allowed. Got: {file_ext}"
        )
    
    if not file.content_type or "pdf" not in file.content_type.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type. Expected PDF, got: {file.content_type}"
        )


def load_and_split_pdf(path: str) -> list:
    """
    Load PDF and split into chunks using RecursiveCharacterTextSplitter
    
    Args:
        path: Path to the PDF file
        
    Returns:
        List of document chunks
        
    Raises:
        ValueError: If no content can be extracted
        Exception: For other processing errors
    """
    try:
        # Load PDF documents
        loader = PyPDFLoader(file_path=path)
        documents = loader.load()
        logger.info(f"Loaded {len(documents)} pages from PDF")
        
        if not documents:
            raise ValueError("No content extracted from PDF")
        
        # Split text into chunks with better strategy
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Split into {len(chunks)} chunks")
        
        return chunks
    except Exception as e:
        logger.error(f"Error loading and splitting PDF: {str(e)}")
        raise


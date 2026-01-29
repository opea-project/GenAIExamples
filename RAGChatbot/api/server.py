"""
FastAPI server with routes for RAG Chatbot API
"""

import os
import tempfile
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

import config
from models import (
    QueryRequest, UploadResponse, QueryResponse,
    HealthResponse, DeleteResponse
)
from services import (
    validate_pdf_file, load_and_split_pdf,
    store_in_vector_storage, load_vector_store, delete_vector_store,
    query_documents
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app"""
    # Startup
    app.state.vectorstore = load_vector_store(config.INFERENCE_API_TOKEN)
    if app.state.vectorstore:
        logger.info("✓ FAISS vector store loaded successfully")
    else:
        logger.info("! No existing vector store found. Please upload a PDF document.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG Chatbot API")


# Initialize FastAPI app
app = FastAPI(
    title=config.APP_TITLE,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOW_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
)


# ==================== Routes ====================

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": "RAG Chatbot API is running",
        "version": config.APP_VERSION,
        "status": "healthy",
        "vectorstore_loaded": app.state.vectorstore is not None
    }


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Detailed health check"""
    return HealthResponse(
        status="healthy",
        vectorstore_available=app.state.vectorstore is not None,
        openai_key_configured=bool(config.INFERENCE_API_TOKEN)
    )


@app.post("/upload-pdf", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file, process it, create embeddings, and store in FAISS
    
    - **file**: PDF file to upload (max 50MB)
    """
    # Validate file
    validate_pdf_file(file)
    
    tmp_path = None
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Check file size
        if file_size > config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {config.MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
            )
        
        logger.info(f"Processing PDF: {file.filename} ({file_size / 1024:.2f} KB)")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
            logger.info(f"Saved to temporary path: {tmp_path}")
        
        # Load and split PDF
        chunks = load_and_split_pdf(tmp_path)
        
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text content could be extracted from the PDF"
            )
        
        # Create embeddings and store in FAISS
        vectorstore = store_in_vector_storage(chunks, config.INFERENCE_API_TOKEN)
        
        # Update app state
        app.state.vectorstore = vectorstore
        
        logger.info(f"✓ Successfully processed PDF: {file.filename}")
        
        return UploadResponse(
            message=f"Successfully uploaded and processed '{file.filename}'",
            num_chunks=len(chunks),
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.info(f"Cleaned up temporary file: {tmp_path}")
            except Exception as e:
                logger.warning(f"Could not remove temporary file: {str(e)}")


@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    """
    Query the uploaded documents using RAG
    
    - **query**: Natural language question about the documents
    """
    if not app.state.vectorstore:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents uploaded. Please upload a PDF first using /upload-pdf endpoint."
        )
    
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )
    
    try:
        result = query_documents(
            request.query,
            app.state.vectorstore,
            config.INFERENCE_API_TOKEN
        )
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@app.delete("/vectorstore", response_model=DeleteResponse)
def delete_vectorstore_endpoint():
    """Delete the current vector store"""
    try:
        deleted = delete_vector_store()
        app.state.vectorstore = None
        
        if deleted:
            return DeleteResponse(
                message="Vector store deleted successfully",
                status="success"
            )
        else:
            return DeleteResponse(
                message="No vector store found to delete",
                status="success"
            )
    except Exception as e:
        logger.error(f"Error deleting vector store: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting vector store: {str(e)}"
        )


# Entry point for running with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)


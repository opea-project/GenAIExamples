"""
FastAPI server with routes for Multi-Agent Q&A API
"""

import logging
import os
import tempfile
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

import config
from models import (
    ChatRequest, ChatResponse, HealthResponse, 
    AgentConfigs, ConfigResponse
)
from services import process_query, update_agent_configs
from services.rag_service import get_rag_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory log store for agent activity
agent_activity_logs = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app"""
    # Startup
    logger.info("Initializing Multi-Agent Q&A API")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Multi-Agent Q&A API")


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
        "message": "Multi-Agent Q&A API is running",
        "version": config.APP_VERSION,
        "status": "healthy"
    }


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Detailed health check"""
    api_configured = bool(config.INFERENCE_API_TOKEN)
    return HealthResponse(
        status="healthy",
        api_configured=api_configured
    )


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    Process a chat message using the multi-agent system
    
    - **message**: User message/query
    - **agent_config**: Optional agent configuration override
    """
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )
    
    try:
        # Process the query with the appropriate agent
        response, agent = process_query(
            query=request.message,
            agent_config=request.agent_config
        )
        
        return ChatResponse(
            response=response,
            agent=agent
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/config", response_model=ConfigResponse)
def get_config():
    """Get current agent configuration"""
    from services.agents import (
        DEFAULT_ORCHESTRATION_CONFIG,
        DEFAULT_CODE_CONFIG,
        DEFAULT_RAG_CONFIG,
        DEFAULT_NORMAL_CONFIG
    )
    
    return ConfigResponse(
        config={
            "orchestration": DEFAULT_ORCHESTRATION_CONFIG,
            "code": DEFAULT_CODE_CONFIG,
            "rag": DEFAULT_RAG_CONFIG,
            "normal": DEFAULT_NORMAL_CONFIG
        }
    )


@app.post("/config")
def update_config(configs: AgentConfigs):
    """Update agent configurations"""
    try:
        config_dict = {}
        
        if configs.orchestration:
            config_dict["orchestration"] = {
                "role": configs.orchestration.role,
                "goal": configs.orchestration.goal,
                "backstory": configs.orchestration.backstory,
                "max_iter": configs.orchestration.max_iter,
                "verbose": configs.orchestration.verbose
            }
        
        if configs.code:
            config_dict["code"] = {
                "role": configs.code.role,
                "goal": configs.code.goal,
                "backstory": configs.code.backstory,
                "max_iter": configs.code.max_iter,
                "verbose": configs.code.verbose
            }
        
        if configs.rag:
            config_dict["rag"] = {
                "role": configs.rag.role,
                "goal": configs.rag.goal,
                "backstory": configs.rag.backstory,
                "max_iter": configs.rag.max_iter,
                "verbose": configs.rag.verbose
            }
        
        if configs.normal:
            config_dict["normal"] = {
                "role": configs.normal.role,
                "goal": configs.normal.goal,
                "backstory": configs.normal.backstory,
                "max_iter": configs.normal.max_iter,
                "verbose": configs.normal.verbose
            }
        
        update_agent_configs(config_dict)
        
        return {"message": "Configuration updated successfully", "status": "success"}
        
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating configuration: {str(e)}"
        )


@app.get("/logs")
def get_logs():
    """Get agent activity logs"""
    from services.agents import activity_logs
    
    # Return last 100 logs
    return {
        "logs": activity_logs[-100:],
        "total": len(activity_logs)
    }


@app.post("/rag/upload")
def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and build RAG index
    
    - **file**: PDF file to upload and index
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = file.file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Process PDF
            rag_service = get_rag_service()
            chunks = rag_service.process_pdf(tmp_path)
            
            # Build index
            rag_service.build_index(chunks)
            
            logger.info(f"Successfully indexed {len(chunks)} chunks from {file.filename}")
            
            return {
                "message": f"Successfully uploaded and indexed PDF: {file.filename}",
                "filename": file.filename,
                "chunks": len(chunks),
                "status": "success"
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF: {str(e)}"
        )


@app.get("/rag/status")
def get_rag_status():
    """Get RAG index status"""
    try:
        rag_service = get_rag_service()
        status_info = rag_service.get_status()
        return status_info
    except Exception as e:
        logger.error(f"Error getting RAG status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting status: {str(e)}"
        )


@app.delete("/rag/index")
def delete_rag_index():
    """Delete the RAG index"""
    try:
        rag_service = get_rag_service()
        deleted = rag_service.delete_index()
        return {
            "message": "RAG index deleted successfully" if deleted else "No index to delete",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error deleting RAG index: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting index: {str(e)}"
        )


# Entry point for running with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)


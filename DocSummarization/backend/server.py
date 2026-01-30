"""
FastAPI server for Doc-Sum Application
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import config
from models import HealthResponse
from api.routes import router

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=config.APP_TITLE,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOW_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
)

# Include API routes
app.include_router(router)

# Root endpoint
@app.get("/")
def root():
    """Root endpoint with service info"""
    return {
        "message": "Document Summarization Service is running",
        "version": config.APP_VERSION,
        "status": "healthy",
        "docs": "/docs",
        "health": "/health",
        "config": {
            "llm_provider": "Enterprise Inference (Token-based)",
            "llm_model": config.INFERENCE_MODEL_NAME
        }
    }

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
def health_check():
    """Detailed health check - checks service configuration"""
    return HealthResponse(
        status="healthy",
        service=config.APP_TITLE,
        version=config.APP_VERSION,
        llm_provider="Enterprise Inference (Token-based)"
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Log configuration on startup"""
    logger.info("=" * 60)
    logger.info(f"Starting {config.APP_TITLE} v{config.APP_VERSION}")
    logger.info("=" * 60)
    logger.info("LLM Provider: Enterprise Inference (Token-based)")
    logger.info(f"Inference Endpoint: {config.INFERENCE_API_ENDPOINT}")
    logger.info(f"Model: {config.INFERENCE_MODEL_NAME}")
    logger.info(f"Port: {config.SERVICE_PORT}")
    logger.info("=" * 60)

# Entry point for running with uvicorn
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.SERVICE_PORT,
        timeout_keep_alive=300
    )

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
    allow_origins=config.CORS_ORIGINS.split(",") if config.CORS_ORIGINS != "*" else ["*"],
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
    response = {
        "message": "Document Summarization Service is running",
        "version": config.APP_VERSION,
        "status": "healthy",
        "docs": "/docs",
        "health": "/health"
    }

    # Only show config if services are actually configured
    if config.BASE_URL and config.KEYCLOAK_CLIENT_SECRET:
        response["config"] = {
            "llm_provider": "Enterprise Inference (Keycloak)",
            "llm_model": config.INFERENCE_MODEL_NAME
        }

    return response

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
def health_check():
    """Detailed health check - dynamically checks service configuration"""
    response_data = {
        "status": "healthy",
        "service": config.APP_TITLE,
        "version": config.APP_VERSION
    }

    # Only show llm_provider if Keycloak is actually configured
    if config.BASE_URL and config.KEYCLOAK_CLIENT_SECRET:
        response_data["llm_provider"] = "Enterprise Inference (Keycloak)"

    return HealthResponse(**response_data)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Log configuration on startup"""
    logger.info("=" * 60)
    logger.info(f"Starting {config.APP_TITLE} v{config.APP_VERSION}")
    logger.info("=" * 60)
    logger.info("LLM Provider: Enterprise Inference (Keycloak)")
    logger.info(f"Base URL: {config.BASE_URL}")
    logger.info(f"Keycloak Configured: {bool(config.KEYCLOAK_CLIENT_SECRET)}")
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

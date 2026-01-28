from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os

from app.api.routes import router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LLM Script Generation Service",
    description="Generate podcast scripts from text using AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, tags=["Script Generation"])

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("=" * 60)
    logger.info("LLM Script Generation Service starting up...")
    logger.info("=" * 60)
    logger.info(f"Service running on port {settings.SERVICE_PORT}")

    if settings.INFERENCE_API_ENDPOINT and settings.INFERENCE_API_TOKEN:
        logger.info("LLM Provider: Inference API")
        logger.info(f"Inference API Endpoint: {settings.INFERENCE_API_ENDPOINT}")
        logger.info(f"Model: {settings.INFERENCE_MODEL_NAME}")
    else:
        logger.error("INFERENCE_API_ENDPOINT and INFERENCE_API_TOKEN are required")
        raise ValueError("Inference API configuration missing")

    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("LLM Script Generation Service shutting down...")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LLM Script Generation Service",
        "version": "1.0.0",
        "description": "Convert text content into engaging podcast dialogue",
        "config": {
            "llm_provider": "Inference API",
            "llm_model": settings.INFERENCE_MODEL_NAME
        },
        "endpoints": {
            "generate_script": "POST /generate-script - Generate podcast script",
            "refine_script": "POST /refine-script - Refine existing script",
            "validate_content": "POST /validate-content - Validate content suitability",
            "health": "GET /health - Health check",
            "tones": "GET /tones - Available conversation tones",
            "models": "GET /models - Available LLM models",
            "docs": "GET /docs - API documentation"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT)

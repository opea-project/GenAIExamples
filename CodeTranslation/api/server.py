"""
FastAPI server with routes for Code Translation API
"""

import os
import tempfile
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

import config
from models import (
    TranslateRequest, TranslateResponse, UploadPdfResponse,
    HealthResponse, SupportedLanguagesResponse
)
from services import (
    get_api_client, extract_code_from_pdf, validate_pdf_file
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
    try:
        api_client = get_api_client()
        app.state.api_client = api_client
        logger.info("API client initialized with inference endpoint")
    except Exception as e:
        logger.error(f"Failed to initialize API client: {str(e)}")
        app.state.api_client = None

    yield

    # Shutdown
    logger.info("Shutting down Code Translation API")


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
    """Root endpoint"""
    return {
        "message": "Code Translation API is running",
        "version": config.APP_VERSION,
        "status": "healthy",
        "api_client_authenticated": app.state.api_client is not None
    }


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Detailed health check"""
    return HealthResponse(
        status="healthy",
        model_configured=bool(config.INFERENCE_MODEL_NAME),
        inference_authenticated=app.state.api_client is not None and app.state.api_client.is_authenticated()
    )


@app.get("/languages", response_model=SupportedLanguagesResponse)
def get_supported_languages():
    """Get list of supported programming languages"""
    return SupportedLanguagesResponse(
        languages=config.SUPPORTED_LANGUAGES
    )


@app.post("/translate", response_model=TranslateResponse)
def translate_code_endpoint(request: TranslateRequest):
    """
    Translate code from one language to another

    - **source_code**: Code to translate
    - **source_language**: Source programming language (java, c, cpp, python, rust, go)
    - **target_language**: Target programming language (java, c, cpp, python, rust, go)
    """
    if not app.state.api_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API client not initialized. Check inference API configuration."
        )

    # Validate languages
    if request.source_language.lower() not in config.SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source language '{request.source_language}' not supported. Supported: {', '.join(config.SUPPORTED_LANGUAGES)}"
        )

    if request.target_language.lower() not in config.SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target language '{request.target_language}' not supported. Supported: {', '.join(config.SUPPORTED_LANGUAGES)}"
        )

    # Check code length
    if len(request.source_code) > config.MAX_CODE_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Code too long. Maximum length is {config.MAX_CODE_LENGTH} characters"
        )

    try:
        logger.info(f"Translating code from {request.source_language} to {request.target_language}")

        # Translate code using API client
        translated_code = app.state.api_client.translate_code(
            source_code=request.source_code,
            source_lang=request.source_language,
            target_lang=request.target_language
        )

        if not translated_code:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Translation failed. No output received from model."
            )

        logger.info(f"Successfully translated code")

        return TranslateResponse(
            translated_code=translated_code,
            source_language=request.source_language,
            target_language=request.target_language,
            original_code=request.source_code
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error translating code: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error translating code: {str(e)}"
        )


@app.post("/upload-pdf", response_model=UploadPdfResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and extract code from it

    - **file**: PDF file containing code (max 10MB)
    """
    tmp_path = None
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate file
        validate_pdf_file(file.filename, file_size, config.MAX_FILE_SIZE)

        logger.info(f"Processing PDF: {file.filename} ({file_size / 1024:.2f} KB)")

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
            logger.info(f"Saved to temporary path: {tmp_path}")

        # Extract code from PDF
        extracted_code = extract_code_from_pdf(tmp_path)

        if not extracted_code.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No code content could be extracted from the PDF"
            )

        logger.info(f"Successfully extracted code from PDF: {file.filename}")

        return UploadPdfResponse(
            message=f"Successfully extracted code from '{file.filename}'",
            extracted_code=extracted_code,
            status="success"
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
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


# Entry point for running with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)

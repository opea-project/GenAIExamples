from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import logging

from app.core.dialogue_generator import DialogueGenerator
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize dialogue generator
dialogue_generator = DialogueGenerator()

class GenerateScriptRequest(BaseModel):
    text: str = Field(..., description="PDF content to convert")
    host_name: str = Field(default="Host", description="Host name")
    guest_name: str = Field(default="Guest", description="Guest name")
    tone: str = Field(default="conversational", description="Conversation tone")
    max_length: int = Field(default=2000, description="Target word count")
    provider: str = Field(default="inference", description="LLM provider")
    job_id: Optional[str] = Field(default=None, description="Optional job ID")

class RefineScriptRequest(BaseModel):
    script: List[Dict[str, str]] = Field(..., description="Script to refine")
    provider: str = Field(default="inference", description="LLM provider")

class ValidateContentRequest(BaseModel):
    text: str = Field(..., description="Content to validate")

class ScriptResponse(BaseModel):
    script: List[Dict[str, str]]
    metadata: Dict
    status: str

class ValidationResponse(BaseModel):
    valid: bool
    word_count: int
    char_count: int
    token_count: int
    issues: List[str]
    recommendations: List[str]

class HealthResponse(BaseModel):
    status: str
    llm_available: bool
    llm_provider: str
    version: str

@router.post("/generate-script", response_model=ScriptResponse)
async def generate_script(request: GenerateScriptRequest):
    """
    Generate podcast script from text content

    - **text**: Source content from PDF
    - **host_name**: Name for the host (default: "Host")
    - **guest_name**: Name for the guest (default: "Guest")
    - **tone**: Conversation tone (conversational/educational/professional)
    - **max_length**: Target word count (default: 2000)
    - **provider**: LLM provider (default: inference)
    - **job_id**: Optional job ID for tracking

    Returns podcast script with metadata
    """
    try:
        logger.info(f"Generating script: tone={request.tone}, provider={request.provider}")

        result = await dialogue_generator.generate_script(
            text=request.text,
            host_name=request.host_name,
            guest_name=request.guest_name,
            tone=request.tone,
            max_length=request.max_length,
            provider=request.provider
        )

        if request.job_id:
            result["metadata"]["job_id"] = request.job_id

        return ScriptResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Script generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Script generation failed: {str(e)}"
        )

@router.post("/refine-script", response_model=ScriptResponse)
async def refine_script(request: RefineScriptRequest):
    """
    Refine an existing podcast script

    - **script**: Current script to refine
    - **provider**: LLM provider (default: inference)

    Returns refined script with metadata
    """
    try:
        logger.info(f"Refining script with {len(request.script)} turns")

        result = await dialogue_generator.refine_script(
            script=request.script,
            provider=request.provider
        )

        return ScriptResponse(**result)

    except Exception as e:
        logger.error(f"Script refinement failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Script refinement failed: {str(e)}"
        )

@router.post("/validate-content", response_model=ValidationResponse)
async def validate_content(request: ValidateContentRequest):
    """
    Validate if content is suitable for podcast generation

    - **text**: Content to validate

    Returns validation results with recommendations
    """
    try:
        result = dialogue_generator.validate_content_length(request.text)
        return ValidationResponse(**result)

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and inference API availability"""
    llm_available = dialogue_generator.llm_client.is_available()

    return HealthResponse(
        status="healthy" if llm_available else "degraded",
        llm_available=llm_available,
        llm_provider="Inference API",
        version="1.0.0"
    )

@router.get("/tones")
async def get_available_tones():
    """Get list of available conversation tones"""
    return {
        "tones": [
            {
                "id": "conversational",
                "name": "Conversational",
                "description": "Warm, friendly, and accessible conversation"
            },
            {
                "id": "educational",
                "name": "Educational",
                "description": "Informative and structured learning experience"
            },
            {
                "id": "professional",
                "name": "Professional",
                "description": "Polished and authoritative discussion"
            }
        ],
        "default": "conversational"
    }

@router.get("/models")
async def get_available_models():
    """Get configured inference model"""
    return {
        "model": settings.INFERENCE_MODEL_NAME,
        "provider": "Inference API"
    }

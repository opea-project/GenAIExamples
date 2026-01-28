"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional


class TranslateRequest(BaseModel):
    """Request model for code translation"""
    source_code: str = Field(..., min_length=1, description="Source code to translate")
    source_language: str = Field(..., description="Source programming language")
    target_language: str = Field(..., description="Target programming language")

    class Config:
        json_schema_extra = {
            "example": {
                "source_code": "def hello():\n    print('Hello World')",
                "source_language": "python",
                "target_language": "java"
            }
        }


class TranslateResponse(BaseModel):
    """Response model for code translation"""
    translated_code: str = Field(..., description="Translated code")
    source_language: str = Field(..., description="Source language")
    target_language: str = Field(..., description="Target language")
    original_code: str = Field(..., description="Original source code")

    class Config:
        json_schema_extra = {
            "example": {
                "translated_code": "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello World\");\n    }\n}",
                "source_language": "python",
                "target_language": "java",
                "original_code": "def hello():\n    print('Hello World')"
            }
        }


class UploadPdfResponse(BaseModel):
    """Response model for PDF upload"""
    message: str = Field(..., description="Success message")
    extracted_code: str = Field(..., description="Extracted code from PDF")
    status: str = Field(..., description="Operation status")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Successfully extracted code from 'code.pdf'",
                "extracted_code": "def hello():\n    print('Hello World')",
                "status": "success"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Health status")
    model_configured: bool = Field(..., description="Whether model is configured")
    inference_authenticated: bool = Field(..., description="Whether inference API auth is successful")


class SupportedLanguagesResponse(BaseModel):
    """Response model for supported languages"""
    languages: list[str] = Field(..., description="List of supported programming languages")

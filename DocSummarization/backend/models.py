"""
Data Models for Doc-Sum API
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class SummarizeRequest(BaseModel):
    """Request model for summarization"""
    type: Literal["text", "pdf"]
    messages: Optional[str] = ""
    max_tokens: int = Field(default=1024, ge=100, le=4000)
    language: str = "en"
    summary_type: str = "auto"
    stream: bool = False


class SummarizeResponse(BaseModel):
    """Response model for summarization"""
    text: str
    summary: str  # Kept for backward compatibility
    word_count: Optional[int] = None
    char_count: Optional[int] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    llm_provider: Optional[str] = None

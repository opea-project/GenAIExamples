"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ChatMessage(BaseModel):
    """Individual chat message"""
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")
    agent: Optional[str] = Field(None, description="Agent that generated the response")


class ChatRequest(BaseModel):
    """Request model for chat messages"""
    message: str = Field(..., min_length=1, description="User message")
    agent_config: Optional[Dict[str, Any]] = Field(None, description="Optional agent configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "How do I implement a recursive function in Python?",
                "agent_config": None
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat messages"""
    response: str = Field(..., description="Agent response")
    agent: str = Field(..., description="Agent that generated the response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "A recursive function calls itself...",
                "agent": "code_agent"
            }
        }


class AgentConfig(BaseModel):
    """Configuration for a single agent"""
    role: str = Field(..., description="Agent role")
    goal: str = Field(..., description="Agent goal")
    backstory: str = Field(..., description="Agent backstory")
    max_iter: Optional[int] = Field(15, description="Maximum iterations")
    verbose: Optional[bool] = Field(True, description="Verbose output")


class AgentConfigs(BaseModel):
    """Configuration for all agents"""
    orchestration: Optional[AgentConfig] = None
    code: Optional[AgentConfig] = None
    rag: Optional[AgentConfig] = None
    normal: Optional[AgentConfig] = None


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Health status")
    api_configured: bool = Field(..., description="Whether API is configured")


class ConfigResponse(BaseModel):
    """Response model for configuration"""
    config: Dict[str, Any] = Field(..., description="Current agent configuration")


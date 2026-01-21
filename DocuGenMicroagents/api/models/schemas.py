"""
Pydantic schemas for API requests and responses
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, HttpUrl, Field


class GenerateDocsRequest(BaseModel):
    """Request to generate documentation"""
    repo_url: HttpUrl = Field(..., description="GitHub repository URL")


class GenerateDocsResponse(BaseModel):
    """Response with job ID for tracking"""
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Job status information"""
    job_id: str
    status: str
    progress_percentage: int
    current_agent: Optional[str] = None
    error_message: Optional[str] = None
    readme_preview: Optional[str] = None
    awaiting_project_selection: Optional[bool] = False
    detected_projects: Optional[List[Dict[str, Any]]] = None
    skipped_folders: Optional[List[Dict[str, Any]]] = None


class ProjectSelectionRequest(BaseModel):
    """User's project selection"""
    selected_project_paths: List[str] = Field(..., description="List of selected project paths")


class ProjectSelectionResponse(BaseModel):
    """Response after project selection"""
    status: str
    message: str


class LogType(str, Enum):
    """Types of log entries"""
    AGENT_START = "agent_start"
    AGENT_THINKING = "agent_thinking"
    AGENT_ACTION = "agent_action"  # Agent calling a tool (ReAct Action step)
    AGENT_OBSERVATION = "agent_observation"  # Agent receiving tool result (ReAct Observation step)
    AGENT_TOOL_USE = "agent_tool_use"
    AGENT_DECISION = "agent_decision"
    AGENT_COMPLETE = "agent_complete"
    WORKFLOW_PROGRESS = "workflow_progress"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class AgentLog(BaseModel):
    """Agent activity log entry"""
    timestamp: datetime = Field(default_factory=datetime.now)
    job_id: str
    log_type: LogType
    agent_name: Optional[str] = None
    message: str
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

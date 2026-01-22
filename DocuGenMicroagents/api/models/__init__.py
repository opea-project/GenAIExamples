"""
Data models for DocuGen AI
"""

from .state import DocGenState
from .schemas import (
    GenerateDocsRequest,
    GenerateDocsResponse,
    JobStatusResponse,
    ProjectSelectionRequest,
    ProjectSelectionResponse,
    AgentLog,
    LogType
)
from .log_manager import LogManager, get_log_manager

__all__ = [
    "DocGenState",
    "GenerateDocsRequest",
    "GenerateDocsResponse",
    "JobStatusResponse",
    "ProjectSelectionRequest",
    "ProjectSelectionResponse",
    "AgentLog",
    "LogType",
    "LogManager",
    "get_log_manager"
]

"""
Services module for Multi-Agent Q&A
"""

from .api_client import get_api_client, APIClient
from .agents import (
    get_orchestration_agent, 
    get_code_agent, 
    get_rag_agent, 
    get_normal_agent,
    update_agent_configs,
    process_query
)

__all__ = [
    "get_api_client",
    "APIClient",
    "get_orchestration_agent",
    "get_code_agent",
    "get_rag_agent",
    "get_normal_agent",
    "update_agent_configs",
    "process_query"
]


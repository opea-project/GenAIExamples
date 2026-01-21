"""
LangChain Agents for DocuGen AI
Each agent is autonomous with its own tools and reasoning capabilities
"""

# 10-agent simplified system (optimized for 8K context)
from .code_explorer_agent import run_code_explorer_agent
from .api_reference_agent import run_api_reference_agent
from .call_graph_agent import run_call_graph_agent
from .error_analysis_agent import run_error_analysis_agent
from .env_config_agent import run_env_config_agent
from .dependency_analyzer_agent import run_dependency_analyzer_agent
from .planner_agent import run_planner_agent
from .writer_agent_sectioned import run_writer_agent_sectioned
from .mermaid_agent import run_mermaid_agent
from .qa_validator_agent import run_qa_validator_agent

# PR Agent for MCP
from .pr_agent_mcp import create_pr_with_mcp

__all__ = [
    # Simplified micro-agents
    "run_code_explorer_agent",
    "run_api_reference_agent",
    "run_call_graph_agent",
    "run_error_analysis_agent",
    "run_env_config_agent",
    "run_dependency_analyzer_agent",
    "run_planner_agent",
    "run_writer_agent_sectioned",
    "run_mermaid_agent",
    "run_qa_validator_agent",
    # MCP PR agent
    "create_pr_with_mcp"
]

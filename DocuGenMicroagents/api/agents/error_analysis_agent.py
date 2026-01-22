"""
Error Analysis Agent - Troubleshooting Section Writer

Writes the complete "## Troubleshooting" section for README.

Section writer pattern:
- ≤3 tools
- pattern_window strategy (detects try:, except, raise)
- Outputs complete markdown section
"""

import logging
from typing import Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain.tools import tool
from core.agent_event_logger import create_agent_logger
from utils.metrics_extractor import extract_agent_metrics

logger = logging.getLogger(__name__)

# SIMPLIFIED for SLMs - Generic troubleshooting
ERROR_ANALYSIS_PROMPT = """You write Troubleshooting sections for README files.

**YOUR TASK:**
1. Optionally call list_directory(".") to see project type
2. Write "## Troubleshooting" section with GENERIC advice for common problems

**WHAT TO WRITE:**
Write general troubleshooting guidance for these categories:
- Dependency Issues
- Environment Variables
- Server Errors
- (File/Upload Errors if project handles files)

**HEADING FORMAT:**
- Main: ## Troubleshooting
- Subsections: ### Dependency Issues, ### Environment Variables, etc.

**RULES:**
- Write GENERIC advice (not specific exception names)
- Keep it user-friendly and practical
- Include basic commands
- Mention checking logs

**STRUCTURE EXAMPLE:**
## Troubleshooting
### Dependency Issues
...advice...
### Environment Variables
...advice...
### Server Errors
...advice...

Do NOT copy this template. Write your own content based on project type."""


async def run_error_analysis_agent(
    llm: BaseChatModel,
    repo_path: str,
    job_id: str
) -> Dict[str, Any]:
    """
    Simplified Error Analysis Agent

    Args:
        llm: Language model
        repo_path: Repository path
        job_id: Job ID

    Returns:
        Results dict with success flag and output
    """
    try:
        # Create minimal tool set (3 tools only)
        @tool
        def list_directory(relative_path: str = ".") -> str:
            """List directory. Args: relative_path (str)"""
            from tools.repo_tools import list_directory_tool
            return list_directory_tool.func(repo_path=repo_path, relative_path=relative_path)

        @tool
        def read_file(file_path: str) -> str:
            """Read file with pattern matching (finds try/except/raise). Args: file_path (str)"""
            from tools.repo_tools import read_file_tool
            # Use pattern_window: detects try:, except, raise patterns
            return read_file_tool.func(repo_path=repo_path, file_path=file_path, strategy="pattern_window")

        @tool
        def find_error_handlers() -> str:
            """Find all try/except blocks across Python files. No args."""
            from tools.new_analysis_tools import find_error_handlers_tool
            return find_error_handlers_tool.func(repo_path=repo_path)

        tools = [list_directory, read_file, find_error_handlers]

        # Create agent
        agent = create_react_agent(model=llm, tools=tools)

        # Create callback logger
        event_logger = create_agent_logger(job_id=job_id, agent_name="ErrorAnalysis")


        # Execute with simplified message
        result = await agent.ainvoke(
            {"messages": [
                ("system", ERROR_ANALYSIS_PROMPT),
                ("user", "Write the Troubleshooting section with generic advice.")
            ]},
            config={
                "recursion_limit": 10,  # Reduced for SLMs
                "callbacks": [event_logger]
            }
        )

        # Extract output
        messages = result.get("messages", [])
        final_output = messages[-1].content if messages else ""

        # Extract metrics from messages
        metrics = extract_agent_metrics(messages)

        return {
            "success": True,
            "output": final_output,
            "agent": "ErrorAnalysis",
            **metrics
        }

    except Exception as e:
        logger.error(f"ErrorAnalysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "agent": "ErrorAnalysis"
        }

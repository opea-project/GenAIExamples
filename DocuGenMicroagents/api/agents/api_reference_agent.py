"""
API Reference Agent - SIMPLIFIED for 8K context models

Extracts API endpoints, HTTP methods, parameters, and response models from FastAPI/Flask codebases.

Follows CodeExplorer proven pattern:
- ≤3 tools (minimal schema overhead)
- pattern_window strategy by default (detects @app.get, @router.post)
- Minimal prompt (~200 tokens)
- No inline metrics
"""

import logging
from typing import Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain.tools import tool
from core.agent_event_logger import create_agent_logger
from utils.metrics_extractor import extract_agent_metrics

logger = logging.getLogger(__name__)

# Data Extraction Prompt - outputs JSON data for Mermaid agent, NOT markdown sections
API_REFERENCE_PROMPT = """You are the API Endpoint Data Extractor. Extract API endpoint information for diagram generation.

**YOUR JOB:**
Use tools to find actual API endpoints and extract their data. DO NOT write markdown sections.

**TOOLS:**
- find_entry_points() - find main server files (server.py, main.py, app.py)
- read_file(file_path) - read files (detects @app.get, @router.post, @app.route)
- list_directory(relative_path) - list files

**WORKFLOW:**
1. find_entry_points() to locate server files
2. read_file() on server files to find route decorators
3. Extract: HTTP method, path, description from code

**CRITICAL RULES:**
1. ONLY extract endpoints you actually find in code
2. DO NOT write markdown sections - only return structured data
3. DO NOT invent example endpoints
4. Use actual paths/methods from code

**OUTPUT FORMAT (JSON data structure):**
```json
{
  "endpoints": [
    {
      "method": "GET",
      "path": "/",
      "description": "Health check endpoint"
    },
    {
      "method": "POST",
      "path": "/upload",
      "description": "Upload file for processing"
    }
  ],
  "endpoint_count": 2
}
```

If NO endpoints found:
```json
{
  "endpoints": [],
  "endpoint_count": 0
}
```

Return ONLY the JSON object, nothing else. No markdown, no explanations.

**Limit:** 20 tool calls."""


async def run_api_reference_agent(
    llm: BaseChatModel,
    repo_path: str,
    job_id: str
) -> Dict[str, Any]:
    """
    Simplified API Reference Agent - minimal context usage

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
            """Read file with strategic sampling. Args: file_path (str)"""
            from tools.repo_tools import read_file_tool
            # Use pattern_window strategy to detect FastAPI routes (@app.get, @router.post)
            return read_file_tool.func(repo_path=repo_path, file_path=file_path, strategy="pattern_window")

        @tool
        def find_entry_points() -> str:
            """Find main entry point files (main.py, server.py, app.py). No args."""
            from tools.repo_tools import find_entry_points_tool
            return find_entry_points_tool.func(repo_path=repo_path)

        tools = [list_directory, read_file, find_entry_points]

        # Create agent
        agent = create_react_agent(model=llm, tools=tools)

        # Create callback logger
        event_logger = create_agent_logger(job_id=job_id, agent_name="APIReference")

        # Execute with callback
        result = await agent.ainvoke(
            {"messages": [
                ("system", API_REFERENCE_PROMPT),
                ("user", "Extract API endpoint data as JSON. Start with find_entry_points().")
            ]},
            config={
                "recursion_limit": 20,
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
            "agent": "APIReference",
            **metrics
        }

    except Exception as e:
        logger.error(f"APIReference failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "agent": "APIReference"
        }

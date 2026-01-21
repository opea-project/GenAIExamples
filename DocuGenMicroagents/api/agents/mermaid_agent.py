"""
Mermaid Diagram Agent - SIMPLIFIED for 8K context models

Generates Mermaid diagrams for architecture visualization.

Follows proven pattern:
- ≤3 tools
- Includes validate_mermaid_syntax for self-correction
- Minimal prompt
"""

import logging
from typing import Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain.tools import tool
from core.agent_event_logger import create_agent_logger
from utils.metrics_extractor import extract_agent_metrics

logger = logging.getLogger(__name__)

# MINIMAL system prompt
MERMAID_PROMPT = """You are a Mermaid Diagram Generator. Create architecture diagrams.

**Output:** 1-2 Mermaid diagrams:
1. System Architecture (components and connections)
2. Optional: Data Flow or Sequence Diagram

**Tools:**
- find_entry_points() - find main files
- read_file(path) - read file (smart strategy for structure)
- validate_mermaid_syntax(code) - validate diagram

**Mermaid Rules (CRITICAL):**
- Node IDs: alphanumeric + underscore only (no spaces, slashes)
- Node labels: use quotes for multi-word: NodeID["Label Text"]
- Edge labels: avoid special chars (/, :, `, ")
- Start with: graph TD or flowchart TD

**Example:**
```mermaid
graph TD
    User["User"]
    API["API Server"]
    DB["Database"]
    User -->|Request| API
    API -->|Query| DB
```

**Process:**
1. Find entry points
2. Read key files
3. Generate diagram
4. VALIDATE with validate_mermaid_syntax()
5. Fix errors if validation fails

**Limit:** 12 tool calls."""


async def run_mermaid_agent(
    llm: BaseChatModel,
    repo_path: str,
    job_id: str,
    api_endpoints: list = None
) -> Dict[str, Any]:
    """
    Simplified Mermaid Agent

    Args:
        llm: Language model
        repo_path: Repository path
        job_id: Job ID
        api_endpoints: Optional list of API endpoints extracted by API Reference agent

    Returns:
        Results dict with success flag and output
    """
    try:
        # Create minimal tool set (3 tools)
        @tool
        def find_entry_points() -> str:
            """Find main entry point files. No args."""
            from tools.repo_tools import find_entry_points_tool
            return find_entry_points_tool.func(repo_path=repo_path)

        @tool
        def read_file(file_path: str) -> str:
            """Read file with smart sampling. Args: file_path (str)"""
            from tools.repo_tools import read_file_tool
            # Use smart strategy: signatures only (good for architecture)
            return read_file_tool.func(repo_path=repo_path, file_path=file_path, strategy="smart")

        @tool
        def validate_mermaid_syntax(mermaid_code: str) -> str:
            """Validate Mermaid diagram syntax. Args: mermaid_code (str)"""
            from tools.repo_tools import validate_mermaid_syntax_tool
            return validate_mermaid_syntax_tool.func(mermaid_code=mermaid_code)

        tools = [find_entry_points, read_file, validate_mermaid_syntax]

        # Create agent
        agent = create_react_agent(model=llm, tools=tools)

        # Create callback logger
        event_logger = create_agent_logger(job_id=job_id, agent_name="Mermaid")


        # Build user message with optional API endpoints
        user_message = "Generate Mermaid architecture diagram. Start with find_entry_points()."

        if api_endpoints and len(api_endpoints) > 0:
            user_message += f"\n\nAPI Endpoints available (include these in diagram if relevant):\n"
            for ep in api_endpoints[:10]:  # Limit to 10 to avoid context overflow
                method = ep.get("method", "GET")
                path = ep.get("path", "/")
                desc = ep.get("description", "")
                user_message += f"- {method} {path}: {desc}\n"

        # Execute
        result = await agent.ainvoke(
            {"messages": [
                ("system", MERMAID_PROMPT),
                ("user", user_message)
            ]},
            config={
                "recursion_limit": 15,
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
            "agent": "Mermaid",
            **metrics
        }

    except Exception as e:
        logger.error(f"Mermaid failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "agent": "Mermaid"
        }

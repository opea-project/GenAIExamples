"""
Environment Config Agent - Configuration Section Writer

Writes the complete "## Configuration" section for README.

Section writer pattern:
- ≤3 tools
- full strategy (config files are small)
- Outputs complete markdown section
"""

import logging
from typing import Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain.tools import tool
from core.agent_event_logger import create_agent_logger
from utils.metrics_extractor import extract_agent_metrics

logger = logging.getLogger(__name__)


def _get_final_assistant_text(messages) -> str:
    """
    Extract the last non-empty AIMessage content from LangGraph result.

    FIX: messages[-1] is not guaranteed to be the final assistant answer.
    """
    for m in reversed(messages or []):
        if isinstance(m, AIMessage) and isinstance(getattr(m, "content", None), str):
            txt = m.content.strip()
            if txt:
                return txt
    return (messages[-1].content or "").strip() if messages else ""

# SIMPLIFIED for SLMs - No templates
ENV_CONFIG_PROMPT = """You write Configuration sections for README files.

**YOUR TASK:**
1. Call find_config_files() to find .env or config files
2. If found, call read_file() on the config file to see variable names
3. Write "## Configuration" section documenting the variables

**WHAT TO WRITE:**
- Start with heading: ## Configuration
- If you found config files, list the environment variables
- Group variables by category (Database, API, Server, etc.)
- Use actual variable names from the files
- Use placeholder values like <value> or your_key_here
- If NO config files found, write: "## Configuration\n\nNo environment configuration files found."

**HEADING FORMAT:**
- Use ## for main section: ## Configuration
- Use ### for subsection: ### Environment Variables

**STRUCTURE EXAMPLE:**
## Configuration
### Environment Variables
Create a .env file:
```bash
DATABASE_URL=<value>
API_KEY=<value>
```
**Required:**
- DATABASE_URL - Database connection
- API_KEY - API authentication

Only document variables you actually find. Keep it simple."""


async def run_env_config_agent(
    llm: BaseChatModel,
    repo_path: str,
    job_id: str
) -> Dict[str, Any]:
    """
    Simplified Env Config Agent

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
            """Read config file. Args: file_path (str)"""
            from tools.repo_tools import read_file_tool
            # Use full strategy: config files are small, read everything
            return read_file_tool.func(repo_path=repo_path, file_path=file_path, strategy="full")

        @tool
        def find_config_files() -> str:
            """Find configuration files (.env, config files). No args."""
            from tools.repo_tools import find_config_files_tool
            return find_config_files_tool.func(repo_path=repo_path)

        tools = [list_directory, read_file, find_config_files]

        # Create agent
        agent = create_react_agent(model=llm, tools=tools)

        # Create callback logger
        event_logger = create_agent_logger(job_id=job_id, agent_name="EnvConfig")


        # Execute with simplified message
        result = await agent.ainvoke(
            {"messages": [
                ("system", ENV_CONFIG_PROMPT),
                ("user", "Write the Configuration section. Call find_config_files()")
            ]},
            config={
                "recursion_limit": 8,
                "callbacks": [event_logger]
            }
        )

        # Extract output - FIX: Use helper to get last AIMessage
        messages = result.get("messages", [])
        final_output = _get_final_assistant_text(messages)

        # Extract metrics from messages
        metrics = extract_agent_metrics(messages)

        return {
            "success": True,
            "output": final_output,
            "agent": "EnvConfig",
            **metrics
        }

    except Exception as e:
        logger.error(f"EnvConfig failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "agent": "EnvConfig"
        }

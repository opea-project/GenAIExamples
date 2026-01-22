"""
Planner Agent - SIMPLIFIED for 8K context models

Analyzes project type and plans documentation sections.

Follows proven pattern:
- ≤3 tools
- full strategy for package files (they're small)
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

# MINIMAL system prompt - MATCHES DOCUGEN TEMPLATE
PLANNER_PROMPT = """You are a Documentation Planner. Determine project type and plan sections.

**Task:** Analyze project and output recommended README sections.

**Tools:**
- detect_languages() - get language breakdown
- extract_dependencies() - get dependencies
- find_ui_files() - check for frontend

**SECTION TEMPLATE (from DocuGen):**
Always include base sections: "Project Overview", "Features", "Architecture", "Prerequisites", "Quick Start Deployment", "Troubleshooting"
Add conditionally:
- "User Interface" - if find_ui_files() returns has_ui=true
- "Configuration" - if project has .env or config files

**Output:** JSON with:
```json
{
  "project_type": "fastapi-backend" (or "web app", "CLI tool", etc.),
  "sections": ["Project Overview", "Features", "Architecture", "Prerequisites", "Quick Start Deployment", "User Interface", "Configuration", "Troubleshooting"]
}
```

**Limit:** 8 tool calls."""


async def run_planner_agent(
    llm: BaseChatModel,
    repo_path: str,
    job_id: str
) -> Dict[str, Any]:
    """
    Simplified Planner Agent

    Args:
        llm: Language model
        repo_path: Repository path
        job_id: Job ID

    Returns:
        Results dict with success flag and output
    """
    try:
        # Create minimal tool set (3 core tools + 2 optional)
        @tool
        def detect_languages() -> str:
            """Detect programming languages. No args."""
            from tools.repo_tools import detect_languages_tool
            return detect_languages_tool.func(repo_path=repo_path)

        @tool
        def extract_dependencies() -> str:
            """Extract dependencies from package files. No args."""
            from tools.repo_tools import extract_dependencies_tool
            return extract_dependencies_tool.func(repo_path=repo_path)

        @tool
        def find_ui_files() -> str:
            """Check if project has UI/frontend. No args."""
            from tools.repo_tools import find_ui_files_tool
            return find_ui_files_tool.func(repo_path=repo_path)

        tools = [detect_languages, extract_dependencies, find_ui_files]

        # Create agent
        agent = create_react_agent(model=llm, tools=tools)

        # Create callback logger
        event_logger = create_agent_logger(job_id=job_id, agent_name="Planner")


        # Execute
        result = await agent.ainvoke(
            {"messages": [
                ("system", PLANNER_PROMPT),
                ("user", "Analyze project type and plan README sections using DocuGen template. Start with detect_languages().")
            ]},
            config={
                "recursion_limit": 8,
                "callbacks": [event_logger]
            }
        )

        # Extract output
        messages = result.get("messages", [])
        final_output = messages[-1].content if messages else ""

        # Parse and validate output has correct section names
        import json
        try:
            # Try to extract JSON
            content = final_output.strip()
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            plan = json.loads(content.strip())

            # Ensure sections match DocuGen template
            if "sections" not in plan or not plan["sections"]:
                plan["sections"] = ["Project Overview", "Features", "Architecture", "Prerequisites", "Quick Start Deployment", "Troubleshooting"]

            final_output = json.dumps(plan, indent=2)
        except:
            # Fallback to default DocuGen sections
            plan = {
                "project_type": "Unknown",
                "sections": ["Project Overview", "Features", "Architecture", "Prerequisites", "Quick Start Deployment", "Troubleshooting"]
            }
            final_output = json.dumps(plan, indent=2)

        # Extract metrics from messages
        metrics = extract_agent_metrics(messages)

        return {
            "success": True,
            "output": final_output,
            "agent": "Planner",
            **metrics
        }

    except Exception as e:
        logger.error(f"Planner failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "agent": "Planner"
        }

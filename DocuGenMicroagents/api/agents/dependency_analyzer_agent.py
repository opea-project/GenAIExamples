"""
Dependency Analyzer Agent - Prerequisites & Deployment Section Writer

Writes the complete "## Prerequisites" and "## Quick Start Deployment" sections for README.

Section writer pattern:
- ≤3 tools
- full strategy for package files (they're small)
- Outputs TWO complete markdown sections
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

# SIMPLIFIED Prompt for SLMs - NO templates, just instructions
def _build_dependency_prompt(repo_url: str) -> str:
    """Build prompt with actual repository URL"""
    return f"""You write Prerequisites and Deployment sections for README files.

**REPOSITORY URL:** {repo_url}

**YOUR TASK:**
1. First, call extract_dependencies() and list_directory(".") to see what's in the repo
2. Based on what you find, write TWO sections

**SECTION 1: ## Prerequisites**
- List what needs to be installed (Python, Node.js, Docker)
- Only list if you found the files (requirements.txt = Python, package.json = Node, docker-compose.yml = Docker)
- Keep it short

**SECTION 2: ## Quick Start Deployment**
This section has TWO subsections (use ### for subsections!):

**Subsection A: ### Installation**
- Show how to clone the repository using the ACTUAL URL above
- Tell how to install dependencies you found
- Use actual paths (if found api/requirements.txt, write "cd api && pip install -r requirements.txt")

**Subsection B: ### Running the Application**
- If docker-compose.yml exists, show docker command
- Otherwise, show how to run the entry point you find (server.py, app.py, main.py, etc.)

**CRITICAL FORMATTING:**
- Main sections use ## (two hashtags)
- Subsections use ### (three hashtags)
- Installation and Running are SUBSECTIONS (use ###, NOT ##)
- Use the ACTUAL repository URL provided above, not placeholders

**EXAMPLE STRUCTURE (not the content, just the heading pattern):**
## Prerequisites
...content...

## Quick Start Deployment
### Installation
Clone the repository:
```bash
git clone {repo_url}
cd repo-name
```
...other steps...
### Running the Application
...commands...

Now analyze the repo and write these sections."""


async def run_dependency_analyzer_agent(
    llm: BaseChatModel,
    repo_path: str,
    job_id: str,
    repo_url: str = None
) -> Dict[str, Any]:
    """
    Simplified Dependency Analyzer Agent

    Args:
        llm: Language model
        repo_path: Repository path
        job_id: Job ID
        repo_url: Repository URL (for clone instructions)

    Returns:
        Results dict with success flag and output
    """
    try:
        # Use placeholder if repo_url not provided
        if not repo_url:
            repo_url = "https://github.com/yourusername/your-repo.git"

        # Create tool set with project structure analysis capabilities
        @tool
        def list_directory(relative_path: str = ".") -> str:
            """List files and folders in a directory. Args: relative_path (str)"""
            from tools.repo_tools import list_directory_tool
            return list_directory_tool.func(repo_path=repo_path, relative_path=relative_path)

        @tool
        def find_dependency_files() -> str:
            """Find dependency files (requirements.txt, package.json, etc.). No args."""
            from tools.repo_tools import find_dependency_files_tool
            return find_dependency_files_tool.func(repo_path=repo_path)

        @tool
        def read_file(file_path: str) -> str:
            """Read file with full content. Args: file_path (str)"""
            from tools.repo_tools import read_file_tool
            # Use full strategy: package files are small
            return read_file_tool.func(repo_path=repo_path, file_path=file_path, strategy="full")

        @tool
        def extract_dependencies() -> str:
            """Extract all dependencies from common package files. No args."""
            from tools.repo_tools import extract_dependencies_tool
            return extract_dependencies_tool.func(repo_path=repo_path)

        tools = [list_directory, find_dependency_files, read_file, extract_dependencies]

        # Create agent
        agent = create_react_agent(model=llm, tools=tools)

        # Create callback logger
        event_logger = create_agent_logger(job_id=job_id, agent_name="DependencyAnalyzer")

        # Build prompt with actual repo URL
        prompt = _build_dependency_prompt(repo_url)

        # Execute with simplified user message
        result = await agent.ainvoke(
            {"messages": [
                ("system", prompt),
                ("user", "Write the sections. Start: call extract_dependencies()")
            ]},
            config={
                "recursion_limit": 12,  # Reduced for SLMs: 2-3 tools + reasoning + output
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
            "agent": "DependencyAnalyzer",
            **metrics
        }

    except Exception as e:
        logger.error(f"DependencyAnalyzer failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "agent": "DependencyAnalyzer"
        }

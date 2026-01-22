"""
Code Explorer Agent - Overview & Features Section Writer

Writes the complete "## Project Overview" and "## Features" sections for README.

Section writer pattern:
- ≤3 tools
- pattern_window strategy for quick file analysis
- Outputs TWO complete markdown sections
"""

import logging
from typing import Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain.tools import tool
from core.agent_event_logger import create_agent_logger
from utils.metrics_extractor import extract_agent_metrics

logger = logging.getLogger(__name__)

# Section Writer Prompt - outputs THREE complete sections
EXPLORER_PROMPT = """You are the Overview, Features & User Interface Section Writer. Write THREE complete README sections.

**YOUR JOB:**
Use tools to understand the project structure and purpose, then write Project Overview, Features, and User Interface sections.

**TOOLS:**
- list_directory(relative_path) - list files in directories
- read_file(file_path) - read file with pattern detection
- detect_languages() - get programming languages used

**WORKFLOW:**
1. list_directory('.') to see project structure
2. detect_languages() to understand tech stack
3. read_file() on key files (README.md if exists, main files) to understand purpose
4. Identify user-facing capabilities (not technical implementation)
5. Check for frontend directories (ui/, frontend/, client/, web/, src/)
6. Write ALL THREE sections

**CRITICAL RULES - Project Overview:**
1. 1-3 sentences ONLY
2. Explain WHAT the project does and WHY it exists
3. NO tech stack lists, NO "Repository Information", NO "Primary Language"
4. Focus on user value, not implementation details

**CRITICAL RULES - Features:**
1. ONLY list user-facing capabilities you can confirm from code
2. NO API endpoints (POST /, GET /), NO routes, NO technical implementation
3. Features = what users CAN DO, not how it's built
4. Group by Backend/Frontend if applicable
5. If minimal code → output: "Basic [project type] structure."

**CRITICAL RULES - User Interface:**
1. ONLY write if frontend directory exists (ui/, frontend/, client/, web/)
2. Describe frontend technology used (React, Vue, Angular, vanilla JS)
3. Key UI components or pages found
4. User workflow/experience
5. If NO frontend found → output: "No dedicated user interface. This is a backend/API project."

**OUTPUT FORMAT (THREE complete markdown sections):**
```
## Project Overview

[1-3 sentences describing what this project does and why it's useful]

## Features

**Backend:**
- Feature 1: [Backend capability based on code found]
- Feature 2: [Another backend capability]

**Frontend:**
- Feature 3: [User interface capability]
- Feature 4: [Another UI capability]

## User Interface

The frontend is built with [React/Vue/Angular/etc.] providing [description of UI].

Key interface elements:
- [Component/page 1] - [Purpose]
- [Component/page 2] - [Purpose]

User workflow:
1. [Step 1 in user journey]
2. [Step 2 in user journey]
```

If NO frontend found:
```
## User Interface

No dedicated user interface. This is a backend/API project. Interact with the application through API endpoints or CLI commands.
```

If minimal/empty repo:
```
## Project Overview

Minimal repository with basic project structure.

## Features

Basic project scaffolding. Refer to source files for details.

## User Interface

No user interface implemented yet.
```

Start with "## Project Overview", then "## Features", then "## User Interface".

**Limit:** 25 tool calls."""


async def run_code_explorer_agent(
    llm: BaseChatModel,
    repo_path: str,
    job_id: str
) -> Dict[str, Any]:
    """
    Simplified Code Explorer - minimal context usage

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
            # Use pattern_window strategy to detect FastAPI routes, error handlers, etc.
            return read_file_tool.func(repo_path=repo_path, file_path=file_path, strategy="pattern_window")

        @tool
        def detect_languages() -> str:
            """Detect languages. No args."""
            from tools.repo_tools import detect_languages_tool
            return detect_languages_tool.func(repo_path=repo_path)

        tools = [list_directory, read_file, detect_languages]

        # Create agent
        agent = create_react_agent(model=llm, tools=tools)

        # Create callback logger for ReAct visibility
        event_logger = create_agent_logger(job_id=job_id, agent_name="CodeExplorer")

        # Execute with callback
        result = await agent.ainvoke(
            {"messages": [
                ("system", EXPLORER_PROMPT),
                ("user", "Write the Project Overview, Features, and User Interface sections. Start with list_directory(relative_path='.').")
            ]},
            config={
                "recursion_limit": 25,
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
            "agent": "CodeExplorer",
            **metrics
        }

    except Exception as e:
        logger.error(f"CodeExplorer failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "agent": "CodeExplorer"
        }

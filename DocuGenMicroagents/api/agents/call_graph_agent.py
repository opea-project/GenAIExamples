"""
Call Graph Agent - Architecture Section Writer

Writes the complete "## Architecture" section for README.

Section writer pattern:
- ≤3 tools
- smart strategy (extracts function signatures, not full bodies)
- Outputs complete markdown section
- Also outputs structured call_graph data for Mermaid agent
"""

import logging
from typing import Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain.tools import tool
from core.agent_event_logger import create_agent_logger
from utils.metrics_extractor import extract_agent_metrics

logger = logging.getLogger(__name__)

# Section Writer Prompt - outputs complete "## Architecture" section with explanation
CALL_GRAPH_PROMPT = """You are the Architecture Section Writer. Write the complete "## Architecture" README section with clear explanation.

**YOUR JOB:**
Use tools to analyze code structure and function relationships, then write a clear Architecture section explaining how components work together.

**TOOLS:**
- list_directory(relative_path) - list files
- read_file(file_path) - read file (uses smart strategy for signatures)
- analyze_code_structure(file_path) - get function/class list from Python files

**WORKFLOW:**
1. list_directory() to find main code files
2. analyze_code_structure() to get quick overview of key files
3. read_file() on important files to understand flow
4. Identify: components, layers, data flow, key modules
5. Write the section with explanation + note about diagram

**CRITICAL RULES:**
1. ONLY describe architecture you can see in the code
2. Start with 2-3 sentences explaining the overall architecture
3. Describe how components interact and data flows
4. Add note: "The architecture diagram below visualizes component relationships and data flow."
5. If minimal code found → output: "## Architecture\n\nMinimal codebase. Refer to source files for structure."
6. DO NOT invent components or layers not found in code

**OUTPUT FORMAT (complete markdown section):**
```
## Architecture

[2-3 sentences explaining the overall architecture pattern, e.g., "The application follows a client-server architecture with a FastAPI backend and React frontend. The backend handles data processing and API endpoints, while the frontend provides the user interface. Data flows from user input through the API to backend services and back to the UI."]

### Components

**[Component Name]** (`path/to/file.py`)
- Purpose: [What it does based on code]
- Key functions: [Actual functions found]

**[Another Component]** (`path/to/file.py`)
- Purpose: [What it does based on code]
- Key functions: [Actual functions found]

### Data Flow

1. User → [Entry point] receives [input]
2. [Entry point] → [Module/Service] processes data
3. [Service] → [Database/API] stores/retrieves information
4. Response flows back through the stack to user

The architecture diagram below visualizes these component relationships and data flow.
```

Start your output with "## Architecture" heading. Include the diagram note at the end.

**Limit:** 25 tool calls."""


async def run_call_graph_agent(
    llm: BaseChatModel,
    repo_path: str,
    job_id: str
) -> Dict[str, Any]:
    """
    Simplified Call Graph Agent

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
            """Read file with smart sampling (signatures only). Args: file_path (str)"""
            from tools.repo_tools import read_file_tool
            # Use smart strategy: top + signatures + bottom (good for call graph)
            return read_file_tool.func(repo_path=repo_path, file_path=file_path, strategy="smart")

        @tool
        def analyze_code_structure(file_path: str) -> str:
            """Analyze Python file structure (functions, classes). Args: file_path (str)"""
            from tools.repo_tools import analyze_code_structure_tool
            return analyze_code_structure_tool.func(repo_path=repo_path, file_path=file_path)

        tools = [list_directory, read_file, analyze_code_structure]

        # Create agent
        agent = create_react_agent(model=llm, tools=tools)

        # Create callback logger
        event_logger = create_agent_logger(job_id=job_id, agent_name="CallGraph")


        # Execute
        result = await agent.ainvoke(
            {"messages": [
                ("system", CALL_GRAPH_PROMPT),
                ("user", "Write the Architecture section. Start with list_directory().")
            ]},
            config={
                "recursion_limit": 40,
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
            "agent": "CallGraph",
            **metrics
        }

    except Exception as e:
        logger.error(f"CallGraph failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "agent": "CallGraph"
        }

# DocuGen Micro-Agents - Customization Guide

This documentation covers how to customize the DocuGen Micro-Agents application for organizational workflows, including modifying agent behavior, strategic file sampling, workflow logic, and model configurations.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Summary](#architecture-summary)
3. [Strategic File Sampling](#strategic-file-sampling)
4. [Customizing Section Writer Agents](#customizing-section-writer-agents)
5. [Customizing Coordination Agents](#customizing-coordination-agents)
6. [Customizing Workflow Logic](#customizing-workflow-logic)
7. [Adding Custom Tools](#adding-custom-tools)
8. [Model Configuration](#model-configuration)
9. [Advanced Scenarios](#advanced-scenarios)

---

## Overview

DocuGen Micro-Agents is designed for extension at multiple layers:
- **Prompt engineering** - Modify agent-specific system prompts
- **Strategic sampling** - Configure file reading strategies for context optimization
- **Section customization** - Modify which sections are generated
- **Workflow modification** - Change execution flow, add validation gates
- **Tool extension** - Add custom repository analysis tools
- **Model configuration** - Use different LLM configurations per agent

All customization points are centralized in well-defined files. This guide provides concrete examples for common modification scenarios.

---

## Architecture Summary

### File Structure

```
docugen-microagents/api/
├── agents/
│   ├── code_explorer_agent.py         # Overview + Features writer
│   ├── api_reference_agent.py         # API endpoint extractor
│   ├── call_graph_agent.py            # Architecture writer
│   ├── error_analysis_agent.py        # Troubleshooting writer
│   ├── env_config_agent.py            # Configuration writer
│   ├── dependency_analyzer_agent.py   # Prerequisites + Deployment writer
│   ├── planner_agent.py               # Section selector
│   ├── mermaid_agent.py               # Diagram generator + validator
│   └── qa_validator_agent.py          # Quality assurance
├── tools/
│   └── repo_tools.py                  # Strategic file reading + analysis tools
├── core/
│   └── metrics_collector.py           # Token usage, TPS, duration tracking
├── models/
│   ├── state.py                       # LangGraph state definition
│   └── evidence.py                    # Evidence-based architecture
├── workflow.py                         # LangGraph workflow orchestration
├── config.py                           # Configuration and settings
└── server.py                           # FastAPI server with SSE streaming
```

### Micro-Agent Execution Flow

**Section Writer Agents** (6 agents - write sections directly):
1. **Code Explorer** - Writes "Project Overview" + "Features" sections
2. **API Reference** - Extracts API endpoints (structured data, not markdown)
3. **Call Graph** - Writes "Architecture" section
4. **Error Analysis** - Writes "Troubleshooting" section
5. **Env Config** - Writes "Configuration" section
6. **Dependency Analyzer** - Writes "Prerequisites" + "Quick Start Deployment" sections

**Coordination Agents** (3 agents - orchestration):
7. **Evidence Aggregator** (node, not agent) - Consolidates filesystem evidence
8. **Planner** - Decides which sections to include in final README
9. **Mermaid Generator** - Creates and validates architecture diagram
10. **QA Validator** - Validates sections against evidence, checks for hallucinations

**Post-Workflow:**
11. **Assembly** (node) - Combines sections into final README
12. **PR Agent** (optional) - Creates GitHub pull request via MCP

---

## Strategic File Sampling

**Location:** `docugen-microagents/api/tools/repo_tools.py`

### Understanding Strategic Sampling

The system implements three intelligent file reading strategies to optimize context usage with small language models (Qwen3-4B with 8K context window). All strategies work within a configurable line budget.

**Configuration:**
```python
# In api/config.py
MAX_LINES_PER_FILE: int = 500  # Line budget per file (pattern_window extracts ~150-300 lines)

# In api/.env
MAX_LINES_PER_FILE=500        # Line budget per file (pattern_window strategy extracts ~150-300 lines focusing on key patterns)
```

### Three Strategies

#### 1. Full Strategy (simple)
```python
# Reads first N lines within budget
strategy="full"  # Returns first 500 lines
```

**When to use:**
- Small files (< 200 lines)
- Configuration files
- Simple scripts

**Behavior:**
- Deterministic and simple
- May miss important code at end of file
- Fast execution

#### 2. Smart Strategy (structural)
```python
# Extracts top + function/class signatures + bottom
strategy="smart"  # Returns ~100-200 lines
```

**Logic:**
```python
# From tools/repo_tools.py lines 95-126
def _smart_sample_lines(lines: List[str], max_lines: int):
    top_n = min(50, max_lines)
    bottom_n = min(30, max_lines - top_n)
    middle_budget = max(0, max_lines - top_n - bottom_n)

    # Extract function/class signatures from middle
    sigs = []
    for ln in lines[top_n:len(lines) - bottom_n]:
        if ln.lstrip().startswith(("def ", "async def ", "class ")):
            sigs.append(ln)

    return top + sigs + bottom
```

**When to use:**
- Python modules with many functions
- Class-heavy OOP code
- Preserving file structure overview

**Behavior:**
- Preserves imports (top)
- Captures all function/class signatures
- Includes file ending (bottom)
- Typical extraction: 100-200 lines

#### 3. Pattern Window Strategy (context-aware) ⭐ DEFAULT
```python
# Extracts ±6 lines around high-value patterns
strategy="pattern_window"  # Returns ~150-300 lines
```

**Logic:**
```python
# From tools/repo_tools.py lines 129-222
def _pattern_window_lines(lines: List[str], max_lines: int):
    patterns = [
        r"@app\.(get|post|put|delete)\b",      # FastAPI routes
        r"@router\.(get|post|put|delete)\b",   # FastAPI router
        r"\bAPIRouter\b",                       # Router definitions
        r"\btry:\b",                            # Error handling
        r"\bexcept\b",                          # Exception handlers
        r"\braise\b",                           # Error raising
        r'if __name__\s*==\s*[\'"]__main__[\'"]',  # Entry points
        r"\buvicorn\.run\b",                    # Server startup
        r"\bdef main\(",                        # Main functions
    ]

    # Find all pattern matches
    # Create windows of ±6 lines around each match
    # Merge overlapping windows
    # Return within max_lines budget
```

**When to use:** (DEFAULT for all agents)
- API route files
- Error handling logic
- Entry point detection
- High-value code extraction

**Behavior:**
- Detects FastAPI/Flask routes, error handlers, entry points
- Extracts ±6 lines around each match
- Falls back to smart strategy if no patterns found
- Typical extraction: 150-300 lines
- Maximizes information density

### Customizing Sampling Strategy

#### Example 1: Change Default Strategy for All Agents

```python
# In tools/repo_tools.py, line 912 (Code Explorer binding)
@tool
def read_file(
    file_path: str,
    max_lines: int = None,
    strategy: Literal["full", "smart", "pattern_window"] = "smart"  # Change from "pattern_window"
) -> str:
    """Read a file with smart strategy as default"""
    return read_file_tool.func(
        repo_path=repo_path,
        file_path=file_path,
        max_lines=max_lines,
        strategy=strategy
    )
```

#### Example 2: Add Custom Pattern for Domain-Specific Code

```python
# In tools/repo_tools.py, add to _pattern_window_lines patterns list
def _pattern_window_lines(lines: List[str], max_lines: int):
    patterns = [
        # Existing patterns...
        r"@app\.(get|post|put|delete)\b",

        # NEW: Domain-specific patterns for your organization
        r"@dataclass",                           # Python dataclasses
        r"@celery\.task",                        # Celery background tasks
        r"class\s+\w+\(BaseModel\)",             # Pydantic models
        r"def\s+test_\w+",                       # Test functions
        r"@pytest\.fixture",                     # Pytest fixtures
        r"@tool",                                # LangChain tools
        r"@app\.middleware",                     # Middleware definitions
        r"@app\.exception_handler",              # Exception handlers
    ]
```

#### Example 3: Adjust Line Budget for Larger Context Models

```python
# If using larger models with more context (e.g., 32K context)
# In api/.env
MAX_LINES_PER_FILE=800  # Increase budget for larger models

# Pattern window will extract ~300-500 lines
# Smart strategy will extract ~200-400 lines
```

#### Example 4: Force Full Strategy for Specific File Types

```python
# In tools/repo_tools.py, modify read_file_tool
@tool
def read_file_tool(
    repo_path: str,
    file_path: str,
    max_lines: int = None,
    strategy: Literal["full", "smart", "pattern_window"] = "full"
) -> str:
    """Read file with strategy selection"""
    if max_lines is None:
        max_lines = settings.MAX_LINES_PER_FILE

    # Force full strategy for config files
    if file_path.endswith(('.json', '.yaml', '.yml', '.toml', '.ini')):
        strategy = "full"

    # Force pattern_window for API files
    elif 'routes/' in file_path or 'api/' in file_path:
        strategy = "pattern_window"

    # Original logic continues...
```

---

## Customizing Section Writer Agents

### Code Explorer Agent (Overview + Features Writer)

**Location:** `docugen-microagents/api/agents/code_explorer_agent.py`

The Code Explorer writes two sections directly: "Project Overview" and "Features".

#### Example: Customize Output Format

```python
# In agents/code_explorer_agent.py
CODE_EXPLORER_SYSTEM_PROMPT = """You are an expert Code Explorer agent...

**Output Format (CRITICAL - FOLLOW EXACTLY):**

## Project Overview

[Write 2-3 paragraphs describing the application's purpose, architecture pattern, and value proposition]

## Features

**Backend Features:**
- Feature 1 (with file reference)
- Feature 2 (with evidence from code)
- Feature 3 (extracted from actual implementation)

**Frontend Features:**
- Feature 1 (with component reference)
- Feature 2 (with framework details)

**NEW REQUIREMENT - Security Features:**
- Authentication mechanism (with file:line reference)
- Authorization model (with evidence)
- Data encryption approach (if detected)
"""
```

#### Example: Force Deeper File Analysis

```python
CODE_EXPLORER_SYSTEM_PROMPT = """...

**Required Tool Usage Pattern (ENHANCED):**

1. list_directory(".") - Get root structure
2. detect_languages() - Get language breakdown
3. extract_dependencies() - Get all dependencies
4. read_file("README.md", strategy="full") - Check existing docs
5. read_file("main entry file", strategy="pattern_window") - Analyze entry point

**NEW: Deep Security Analysis**
6. list_directory("auth") or list_directory("middleware") - Find auth code
7. read_file("auth/main.py", strategy="pattern_window") - Extract auth logic
8. read_file(".env.example", strategy="full") - Identify secret requirements

**NEW: API Analysis**
9. list_directory("routes") or list_directory("api") - Find API routes
10. read_file("routes/*.py", strategy="pattern_window") - Extract all endpoints
"""
```

### API Reference Agent (Endpoint Extractor)

**Location:** `docugen-microagents/api/agents/api_reference_agent.py`

This agent extracts API endpoints as structured JSON data (not markdown).

#### Example: Customize Endpoint Extraction Format

```python
# In agents/api_reference_agent.py
API_REFERENCE_SYSTEM_PROMPT = """...

**Output Format (JSON ONLY - NO MARKDOWN):**

```json
{
  "endpoints": [
    {
      "method": "POST",
      "path": "/api/documents",
      "file": "api/routes/documents.py",
      "line": 45,
      "description": "Upload and process document",
      "request_body": "DocumentInput model",
      "response": "DocumentResponse model",
      "auth_required": true,
      "rate_limit": "10/minute"
    }
  ]
}
```

**NEW FIELDS TO EXTRACT:**
- auth_required: Check for @requires_auth, Depends(get_current_user), etc.
- rate_limit: Look for @limiter.limit decorators
- deprecated: Check for @deprecated decorators
"""
```

### Dependency Analyzer Agent (Prerequisites + Deployment Writer)

**Location:** `docugen-microagents/api/agents/dependency_analyzer_agent.py`

#### Example: Add Docker Compose Analysis

```python
DEPENDENCY_ANALYZER_SYSTEM_PROMPT = """...

**Required Analysis:**

1. **Prerequisites Section:**
   - Runtime versions (Python 3.11+, Node 20+, etc.)
   - System dependencies (Redis, PostgreSQL, etc.)
   - API keys and credentials

2. **Quick Start Deployment Section:**
   - Installation commands
   - Setup instructions
   - Running the application

**NEW: Docker Compose Analysis**
3. If docker-compose.yml exists:
   - Read docker-compose.yml with strategy="full"
   - List all services defined
   - Extract port mappings
   - Document volume mounts
   - Include docker-compose up command

   Example output:
   ```markdown
   ## Quick Start Deployment

   ### Docker Deployment (Recommended)

   The application uses Docker Compose with 3 services:
   - backend (FastAPI) - Port 8000
   - frontend (React) - Port 3000
   - database (PostgreSQL) - Port 5432

   \`\`\`bash
   docker-compose up -d
   \`\`\`
   ```
"""
```

---

## Customizing Coordination Agents

### Planner Agent (Section Selector)

**Location:** `docugen-microagents/api/agents/planner_agent.py`

The Planner decides which sections to include in the final README based on project type.

#### Example: Add Custom "Performance" Section

```python
# In agents/planner_agent.py
PLANNER_SYSTEM_PROMPT = """...

**Standard Sections (REQUIRED for ALL projects):**
1. Project Overview
2. Features
3. Architecture
4. Prerequisites
5. Quick Start Deployment

**Conditional Sections (include if applicable):**
6. User Interface - If frontend detected (React, Vue, Angular)
7. Configuration - If .env.example exists
8. Troubleshooting - If error handlers or try/except blocks found

**NEW: Performance Section (conditional)**
9. Performance - Include if:
   - Caching detected (Redis, Memcached dependencies)
   - Performance monitoring (Prometheus, Datadog integrations)
   - Load balancing configuration (nginx.conf, HAProxy)
   - Database optimization (indexes, query optimization comments)
   - CDN configuration (Cloudflare, Fastly)

**Detection Logic for Performance Section:**
```python
# Check for performance indicators
if any(dep in dependencies for dep in ['redis', 'memcached', 'prometheus-client']):
    sections.append("Performance")
if 'nginx.conf' in config_files or 'load_balancer' in directories:
    sections.append("Performance")
```
"""
```

### Mermaid Generator Agent (Diagram Creator)

**Location:** `docugen-microagents/api/agents/mermaid_agent.py`

#### Example: Customize Diagram Style

```python
MERMAID_SYSTEM_PROMPT = """...

**Diagram Requirements:**

1. **Architecture Diagram (graph TB):**
   - Maximum 8-10 nodes
   - Show user flow: User/Client → Frontend → Backend → Database
   - Include external integrations (LLM Provider, Auth Service, etc.)

**NEW: Corporate Color Scheme**
2. **Styling (REQUIRED):**
   ```mermaid
   graph TB
       A[Frontend]:::frontend
       B[Backend API]:::backend
       C[Database]:::database
       D[External Service]:::external

       classDef frontend fill:#3b82f6,stroke:#1e40af,color:#fff
       classDef backend fill:#10b981,stroke:#059669,color:#fff
       classDef database fill:#f59e0b,stroke:#d97706,color:#fff
       classDef external fill:#8b5cf6,stroke:#6d28d9,color:#fff
   ```

3. **Node Naming Rules:**
   - Use service names, not technical jargon
   - Good: "User Authentication", "Document Processor"
   - Bad: "JWT Middleware", "PDF Parser Class"
"""
```

### QA Validator Agent (Quality Assurance)

**Location:** `docugen-microagents/api/agents/qa_validator_agent.py`

#### Example: Add Custom Validation Rules

```python
QA_VALIDATOR_SYSTEM_PROMPT = """...

**Validation Checks (Evidence-Based):**

1. **Hallucination Detection:**
   - Verify all dependencies mentioned exist in evidence.python_deps or evidence.node_deps
   - Verify all environment variables match evidence.env_variables
   - Verify technology stack matches evidence.languages

2. **Completeness Checks:**
   - All sections have > 100 characters
   - Prerequisites lists actual version requirements
   - Configuration section covers all .env.example variables

**NEW: Custom Corporate Validation**
3. **Security Documentation (REQUIRED for ALL projects):**
   - Must mention authentication mechanism (if any)
   - Must document all *_SECRET, *_KEY, *_TOKEN env vars
   - Must warn about credential security

4. **Compliance Check (REQUIRED for enterprise):**
   - If project handles PII: Must mention data protection
   - If project logs data: Must mention audit logging
   - If project uses external APIs: Must mention API key security

**Scoring:**
- Base score: 75
- +5 for each security item documented
- +10 for compliance documentation
- -10 for each hallucination detected
- -5 for incomplete sections
"""
```

---

## Customizing Workflow Logic

**Location:** `docugen-microagents/api/workflow.py`

### Example: Add Approval Gate After Section Writers

Require human approval after all section writers complete, before coordination agents run.

**Step 1:** Add approval state in `models/state.py`:

```python
class DocGenState(TypedDict):
    # Existing fields
    job_id: str
    repo_url: str
    # ...

    # NEW: Approval gate
    sections_approved: Optional[bool]
```

**Step 2:** Add conditional routing in `workflow.py`:

```python
class SimplifiedDocuGenWorkflow:
    async def create_workflow(self) -> StateGraph:
        workflow = StateGraph(DocGenState)

        # Existing nodes...
        workflow.add_node("dependency_analyzer", self.dependency_analyzer_node)
        workflow.add_node("evidence_aggregator", self.evidence_aggregator_node)

        # Add edges
        workflow.add_edge("dependency_analyzer", "evidence_aggregator")

        # NEW: Add approval gate before planner
        workflow.add_conditional_edges(
            "evidence_aggregator",
            self._check_sections_approval,
            {
                "approved": "planner",
                "pending": END  # Pause for approval
            }
        )

    def _check_sections_approval(self, state: DocGenState) -> str:
        """Check if sections were approved"""
        if state.get("sections_approved") is None:
            # First time: pause for approval
            return "pending"
        elif state["sections_approved"]:
            return "approved"
        else:
            # Rejected: end workflow
            return END
```

**Step 3:** Add API endpoint in `server.py`:

```python
@app.post("/api/approve-sections/{job_id}")
async def approve_sections(job_id: str, approved: bool = True):
    """Approve section writer outputs before coordination"""
    workflow = await get_workflow()
    config = {"configurable": {"thread_id": job_id}}

    # Update state with approval
    await workflow.graph.aupdate_state(
        config,
        {"sections_approved": approved}
    )

    if approved:
        # Resume workflow
        async for event in workflow.graph.astream(None, config):
            pass

    return {"status": "approved" if approved else "rejected"}
```

### Example: Skip Mermaid Generation for APIs

```python
def _should_generate_diagram(self, state: DocGenState) -> str:
    """Skip diagrams for API-only projects"""
    evidence = state.get("evidence_packet")

    # Skip if only backend, no frontend
    if evidence and evidence.has_backend and not evidence.has_frontend:
        logger.info("Skipping diagram: API-only project")
        return "skip"

    return "generate"

# In workflow setup:
workflow.add_conditional_edges(
    "planner",
    self._should_generate_diagram,
    {
        "generate": "mermaid",
        "skip": "qa_validator"
    }
)
```

---

## Adding Custom Tools

**Location:** `docugen-microagents/api/tools/repo_tools.py`

### Example: Add Database Schema Extraction Tool

```python
from langchain.tools import tool
import re
from pathlib import Path

@tool
def extract_database_schema_tool(repo_path: str) -> str:
    """
    Extract database schema from SQLAlchemy models or Prisma schema files.

    Args:
        repo_path: Absolute path to repository root

    Returns:
        Formatted database schema with tables and columns
    """
    schema_info = []

    # Check for Prisma schema
    prisma_file = Path(repo_path) / "prisma" / "schema.prisma"
    if prisma_file.exists():
        with open(prisma_file) as f:
            content = f.read()
            models = re.findall(r'model\s+(\w+)\s*\{([^}]+)\}', content, re.DOTALL)
            for model_name, model_body in models:
                fields = re.findall(r'(\w+)\s+(\w+)', model_body)
                schema_info.append(f"Table: {model_name}")
                for field_name, field_type in fields:
                    schema_info.append(f"  - {field_name}: {field_type}")

    # Check for SQLAlchemy models
    models_dir = Path(repo_path) / "models"
    if models_dir.exists():
        for model_file in models_dir.glob("*.py"):
            with open(model_file) as f:
                content = f.read()
                tables = re.findall(r'class\s+(\w+)\([^)]*Base[^)]*\):', content)
                for table in tables:
                    schema_info.append(f"Table: {table} ({model_file.name})")

    if not schema_info:
        return "No database schema files found"

    return "\n".join(schema_info)
```

**Bind tool for agents:**

```python
def make_bound_tools_for_code_explorer(repo_path: str) -> List:
    """Create tools with repo_path pre-bound"""

    @tool
    def extract_database_schema() -> str:
        """Extract database schema. No arguments needed."""
        return extract_database_schema_tool.func(repo_path=repo_path)

    return [
        list_directory,
        read_file,
        detect_languages,
        extract_dependencies,
        extract_database_schema  # NEW
    ]
```

**Update agent prompt:**

```python
CODE_EXPLORER_SYSTEM_PROMPT = """...

**Tool Usage:**
1. list_directory(".")
2. detect_languages()
3. extract_dependencies()
4. extract_database_schema()  # NEW - Get DB schema
5. read_file("main.py", strategy="pattern_window")

**Required Analysis:**
...
4. **Database Schema (if database detected):**
   - Use extract_database_schema() to get table definitions
   - List primary tables and relationships
   - Example: "Database: PostgreSQL with 5 tables (users, documents, sessions, ...)"
"""
```

---

## Model Configuration

**Location:** `docugen-microagents/api/config.py`

### Current Configuration (Qwen3-4B for all agents)

```python
# In .env file
AUTH_MODE=genai_gateway
GENAI_GATEWAY_URL=https://your-gateway-url.com
GENAI_GATEWAY_API_KEY=your-api-key

# All agents use Qwen3-4B-Instruct (optimized for Intel Xeon)
CODE_EXPLORER_MODEL=Qwen/Qwen3-4B-Instruct-2507
API_REFERENCE_MODEL=Qwen/Qwen3-4B-Instruct-2507
CALL_GRAPH_MODEL=Qwen/Qwen3-4B-Instruct-2507
ERROR_ANALYSIS_MODEL=Qwen/Qwen3-4B-Instruct-2507
ENV_CONFIG_MODEL=Qwen/Qwen3-4B-Instruct-2507
DEPENDENCY_ANALYZER_MODEL=Qwen/Qwen3-4B-Instruct-2507
PLANNER_MODEL=Qwen/Qwen3-4B-Instruct-2507
MERMAID_MODEL=Qwen/Qwen3-4B-Instruct-2507
QA_VALIDATOR_MODEL=Qwen/Qwen3-4B-Instruct-2507
WRITER_MODEL=Qwen/Qwen3-4B-Instruct-2507  # Legacy, not used
```

### Example: Use Larger Model for QA Validator

```python
# If you have access to larger models for quality assurance
QA_VALIDATOR_MODEL=Qwen/Qwen2.5-32B-Instruct
```

### Example: Add Custom Model for Compliance Agent

```python
# In config.py
class Settings(BaseSettings):
    # Existing model configs...
    CODE_EXPLORER_MODEL: str = "Qwen/Qwen3-4B-Instruct-2507"

    # NEW: Custom agent model
    COMPLIANCE_MODEL: str = "Qwen/Qwen3-4B-Instruct-2507"
```

---

## Advanced Scenarios

### Scenario 1: Add Compliance Section Writer Agent

**Step 1:** Create `agents/compliance_agent.py`:

```python
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from tools.repo_tools import make_bound_tools_for_code_explorer

COMPLIANCE_SYSTEM_PROMPT = """You are a Compliance Documentation Specialist.

**Your Task:**
Write a comprehensive "Compliance" section for the README.

**Required Content:**
1. Data Classification - What types of data does this system process?
2. Access Controls - Authentication and authorization mechanisms
3. Audit Logging - What actions are logged and where?
4. Encryption - Data at rest and in transit
5. Compliance Frameworks - SOC2, HIPAA, GDPR considerations

**Tools Available:**
- list_directory(path) - List directory contents
- read_file(file_path, strategy) - Read file with strategy
- detect_languages() - Get language breakdown
- extract_dependencies() - Get all dependencies

**Output Format:**

## Compliance

### Data Classification
[Describe what types of data the system processes...]

### Access Controls
[Document authentication and authorization...]

### Audit Logging
[Describe what is logged and retention...]

### Encryption
[Document encryption at rest and in transit...]

### Compliance Frameworks
[List applicable frameworks and how system complies...]
"""

async def run_compliance_agent(llm: BaseChatModel, repo_path: str, job_id: str) -> dict:
    """Run compliance documentation agent"""
    from langchain.agents import create_react_agent, AgentExecutor
    from langchain_core.prompts import PromptTemplate

    # Bind tools
    tools = make_bound_tools_for_code_explorer(repo_path)

    # Create ReAct agent
    agent_prompt = PromptTemplate.from_template("""...React template...""")
    agent = create_react_agent(llm, tools, agent_prompt)

    # Execute
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=15,
        handle_parsing_errors=True
    )

    result = await executor.ainvoke({
        "system_prompt": COMPLIANCE_SYSTEM_PROMPT,
        "repo_path": repo_path
    })

    return {
        "success": True,
        "output": result["output"],
        "input_tokens": 0,  # Extract from result
        "output_tokens": 0,
        "tool_calls": 0,
        "llm_calls": 0
    }
```

**Step 2:** Add node to workflow:

```python
# In workflow.py
from agents.compliance_agent import run_compliance_agent

class SimplifiedDocuGenWorkflow:
    async def create_workflow(self) -> StateGraph:
        # Add compliance node
        workflow.add_node("compliance", self.compliance_node)

        # Insert after dependency_analyzer, before evidence_aggregator
        workflow.add_edge("dependency_analyzer", "compliance")
        workflow.add_edge("compliance", "evidence_aggregator")

    async def compliance_node(self, state: DocGenState) -> DocGenState:
        """Run Compliance agent"""
        job_id = state["job_id"]
        target_path = self._get_target_path(state)

        metrics = self._get_metrics_collector(job_id)
        metrics.start_agent("Compliance")

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message="📋 Running Compliance Writer (7/8)...",
            agent_name="Compliance"
        )

        llm = get_llm(model_name=settings.COMPLIANCE_MODEL, temperature=0.7)
        result = await run_compliance_agent(llm=llm, repo_path=target_path, job_id=job_id)

        if result.get("success"):
            output = result.get("output", "")
            sections_dict = state.get("readme_sections") or {}
            self._parse_and_store_sections(output, sections_dict)
            state["readme_sections"] = sections_dict

            metrics.end_agent(
                "Compliance",
                success=True,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                tool_calls=result.get("tool_calls", 0),
                llm_calls=result.get("llm_calls", 0)
            )
        else:
            metrics.end_agent("Compliance", success=False)

        return state
```

**Step 3:** Add to config:

```python
# In config.py
COMPLIANCE_MODEL: str = "Qwen/Qwen3-4B-Instruct-2507"

# In .env
COMPLIANCE_MODEL=Qwen/Qwen3-4B-Instruct-2507
```

---

## Configuration Reference

### Environment Variables

```bash
# LLM Configuration
AUTH_MODE=genai_gateway
GENAI_GATEWAY_URL=https://your-gateway-url.com
GENAI_GATEWAY_API_KEY=your-api-key

# Micro-Agent Model Configuration (all use Qwen3-4B)
CODE_EXPLORER_MODEL=Qwen/Qwen3-4B-Instruct-2507
API_REFERENCE_MODEL=Qwen/Qwen3-4B-Instruct-2507
CALL_GRAPH_MODEL=Qwen/Qwen3-4B-Instruct-2507
ERROR_ANALYSIS_MODEL=Qwen/Qwen3-4B-Instruct-2507
ENV_CONFIG_MODEL=Qwen/Qwen3-4B-Instruct-2507
DEPENDENCY_ANALYZER_MODEL=Qwen/Qwen3-4B-Instruct-2507
PLANNER_MODEL=Qwen/Qwen3-4B-Instruct-2507
MERMAID_MODEL=Qwen/Qwen3-4B-Instruct-2507
QA_VALIDATOR_MODEL=Qwen/Qwen3-4B-Instruct-2507

# GitHub Integration (MCP)
GITHUB_TOKEN=ghp_...

# Repository Analysis Limits
MAX_REPO_SIZE=10737418240          # 10GB in bytes
MAX_FILE_SIZE=1000000               # 1MB in bytes
MAX_FILES_TO_SCAN=500               # Maximum files to analyze
MAX_LINES_PER_FILE=500              # Line budget per file (pattern_window extracts ~150-300 lines)

# Agent Settings
AGENT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=1000
AGENT_TIMEOUT=300                   # 5 minutes

# Server Configuration
API_PORT=5001
HOST=0.0.0.0
CORS_ORIGINS=["http://localhost:3000"]
```

---

## Testing Customizations

After making customizations, test with representative repositories:

```bash
# Test with different project types
1. Simple web app (React + FastAPI)
2. Complex monorepo (multiple services)
3. API-only service (FastAPI/Spring Boot)
4. CLI tool (Python script)

# Validate outputs:
- Check all custom sections appear
- Verify custom tools are called in logs
- Confirm tone and format match requirements
- Test strategic sampling extracts key patterns
- Verify metrics tracking (tokens, TPS, duration)
- Test with private repos (authentication)
```

Review agent logs in real-time via the UI to debug ReAct reasoning loops, tool usage, and file sampling strategies.

---

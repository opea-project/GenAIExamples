"""
Sectioned Writer Agent - TIMEOUT-RESISTANT DESIGN

Generates README in multiple small calls instead of one large call.

Architecture:
1. Generate outline (fast)
2. Generate sections one-by-one (small, bounded calls)
3. Stitch sections together

This prevents 504 Gateway Timeouts by keeping each LLM call small and fast.
"""

import logging
import json
from typing import Dict, Any, List
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


def build_structured_evidence(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert raw agent outputs into compact structured evidence.

    This dramatically reduces tokens vs raw text concatenation.
    """

    # Parse code summary into bullets
    code_summary = state.get("code_summary", "")
    code_bullets = _extract_bullets(code_summary, max_bullets=10)

    # Parse API documentation
    api_docs = state.get("api_documentation", "")
    api_bullets = _extract_bullets(api_docs, max_bullets=8)

    # Parse dependencies
    dependency_report = state.get("dependency_report", {})
    if isinstance(dependency_report, dict):
        dep_output = dependency_report.get("output", "")
    else:
        dep_output = str(dependency_report)
    dep_bullets = _extract_bullets(dep_output, max_bullets=6)

    # Parse env config
    env_config = state.get("env_config_output", "")
    env_bullets = _extract_bullets(env_config, max_bullets=5)

    # Parse call graph (already dict)
    call_graph = state.get("call_graph", {})
    if isinstance(call_graph, dict) and "output" in call_graph:
        call_graph_text = str(call_graph["output"])[:500]  # Truncate
    else:
        call_graph_text = str(call_graph)[:500]

    # Parse error analysis
    error_analysis = state.get("error_analysis", {})
    if isinstance(error_analysis, dict):
        error_output = error_analysis.get("output", "")
    else:
        error_output = str(error_analysis)
    error_bullets = _extract_bullets(error_output, max_bullets=5)

    # Project metadata
    project_type = state.get("project_type", "Unknown")
    repo_name = state.get("repo_name", "Project")

    # Build compact structured evidence
    structured = {
        "project_name": repo_name,
        "project_type": project_type,
        "overview": code_bullets[:3] if code_bullets else ["No overview available"],
        "architecture": code_bullets[3:8] if len(code_bullets) > 3 else [],
        "api_endpoints": api_bullets,
        "dependencies": dep_bullets,
        "environment": env_bullets,
        "call_graph_summary": call_graph_text,
        "error_handling": error_bullets
    }

    return structured


def _extract_bullets(text: str, max_bullets: int = 10) -> List[str]:
    """Extract bullet points or key sentences from text"""
    if not text:
        return []

    bullets = []

    # Try to find existing bullets (lines starting with -, *, •, or numbers)
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line and (line.startswith('-') or line.startswith('*') or
                     line.startswith('•') or (len(line) > 2 and line[0].isdigit() and line[1] in '.)')):
            # Remove bullet marker
            clean = line.lstrip('-*•0123456789.) ').strip()
            if clean:
                bullets.append(clean)
                if len(bullets) >= max_bullets:
                    break

    # If no bullets found, extract first N sentences
    if not bullets:
        sentences = text.replace('\n', ' ').split('. ')
        for sentence in sentences[:max_bullets]:
            sentence = sentence.strip()
            if sentence:
                bullets.append(sentence)

    return bullets[:max_bullets]


async def run_writer_agent_sectioned(
    llm: BaseChatModel,
    state: Dict[str, Any],
    job_id: str
) -> Dict[str, Any]:
    """
    Sectioned Writer Agent - generates README in multiple small calls.
    Uses planner's section list instead of generating own outline.

    Args:
        llm: Language model
        state: Full workflow state (we'll extract structured evidence)
        job_id: Job ID

    Returns:
        Results dict with sections dict (not a single readme string)
    """
    try:
        # Step 1: Build structured evidence (compact)
        print(f"[Writer] Building structured evidence...")
        evidence = build_structured_evidence(state)
        evidence_json = json.dumps(evidence, indent=2)

        print(f"[Writer] Structured evidence: {len(evidence_json)} chars")
        logger.info(f"[Writer] Structured evidence: {len(evidence_json)} chars")

        # Step 2: Get sections from planner (NO outline generation!)
        planned_sections = state.get("documentation_sections", ["Project Overview", "Features", "Architecture", "Prerequisites", "Quick Start Deployment", "Troubleshooting"])
        print(f"[Writer] Using planner sections: {planned_sections}")
        logger.info(f"[Writer] Using planner sections: {planned_sections}")

        # Step 3: Generate sections one-by-one (small, fast calls)
        sections_dict = {}
        for section_name in planned_sections:
            logger.info(f"[Writer] Generating section: {section_name}")
            section_content = await _generate_section(llm, section_name, evidence)
            # Store with ## heading included
            sections_dict[section_name] = f"## {section_name}\n\n{section_content}"

        logger.info(f"[Writer] Generated {len(sections_dict)} sections")

        # Return sections dict (NOT a single assembled readme)
        # Assembly will happen in assembly_node
        return {
            "success": True,
            "output": sections_dict,  # Dict of section_name: content
            "agent": "Writer"
        }

    except Exception as e:
        logger.error(f"Writer failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "agent": "Writer"
        }


async def _generate_section(
    llm: BaseChatModel,
    section_name: str,
    evidence: Dict[str, Any]
) -> str:
    """
    Generate a single README section (small, fast call).

    Returns: Markdown content for this section
    """

    # Build section-specific evidence (only relevant data)
    # Map DocuGen section names to evidence
    if section_name == "Project Overview":
        context = f"""
Project: {evidence.get('project_name')}
Type: {evidence.get('project_type')}
Overview: {json.dumps(evidence.get('overview', []))}
Architecture: {json.dumps(evidence.get('architecture', [])[:3])}
"""

    elif section_name == "Features":
        context = f"""
Architecture: {json.dumps(evidence.get('architecture', []))}
Key capabilities: {json.dumps(evidence.get('overview', []))}
API Endpoints: {json.dumps(evidence.get('api_endpoints', [])[:5])}
"""

    elif section_name == "Prerequisites":
        context = f"""
Dependencies: {json.dumps(evidence.get('dependencies', []))}
Project type: {evidence.get('project_type')}
"""

    elif section_name == "Quick Start Deployment":
        context = f"""
Dependencies: {json.dumps(evidence.get('dependencies', []))}
Environment variables: {json.dumps(evidence.get('environment', [])[:5])}
Project type: {evidence.get('project_type')}
"""

    elif section_name == "Configuration":
        context = f"""
Environment variables: {json.dumps(evidence.get('environment', []))}
"""

    elif section_name == "User Interface":
        context = f"""
Project type: {evidence.get('project_type')}
Overview: {json.dumps(evidence.get('overview', []))}
"""

    elif section_name == "Architecture":
        context = f"""
Architecture: {json.dumps(evidence.get('architecture', []))}
Call graph: {evidence.get('call_graph_summary', '')}
API Endpoints: {json.dumps(evidence.get('api_endpoints', [])[:3])}
"""

    elif section_name == "Troubleshooting":
        context = f"""
Error handling: {json.dumps(evidence.get('error_handling', []))}
Common issues: {json.dumps(evidence.get('overview', []))}
"""

    else:
        # Fallback for any other section names
        context = json.dumps(evidence, indent=2)[:1000]

    # Section-specific requirements
    if section_name == "Prerequisites":
        requirements = """List ONLY the actual dependencies and requirements found in the context.
Format as:
- Runtime/language versions (e.g., Python 3.8+, Node.js 16+)
- Required tools (Docker, npm, pip, etc.)
- System requirements
If no specific prerequisites found, state: "Standard development environment for [project_type]."
"""
    elif section_name == "Quick Start Deployment":
        requirements = """Provide deployment instructions based ONLY on evidence:
1. Installation steps (based on actual dependencies found)
2. Configuration steps (based on actual env variables found)
3. How to run the application (based on project type and entry points)
4. Docker commands if Docker files were found
If insufficient information, provide minimal: "Refer to dependency files and configuration for setup details."
"""
    elif section_name == "Configuration":
        requirements = """List ONLY the actual environment variables found. Format as:
- Variable name: Brief purpose
If no variables found, state: "No environment configuration required."
"""
    else:
        requirements = "Write based on the evidence provided. Be factual and concise."

    prompt = f"""Write the "{section_name}" section for a README based STRICTLY on the provided evidence.

**CRITICAL RULES:**
1. ONLY use information from the Context below
2. If Context is empty or says "No X available", write a minimal 1-2 sentence section acknowledging what's missing
3. DO NOT invent features, files, commands, or technical details that aren't in the Context
4. DO NOT add placeholder examples or generic instructions
5. Be factual and concise - accuracy over completeness

**Section-Specific Requirements:**
{requirements}

Context:
{context}

Write clear, concise markdown using ONLY the facts above.
If the context indicates the project is minimal/empty, reflect that accurately.
Keep it under 300 words.

Section content:"""

    messages = [
        SystemMessage(content="You are a technical writer who ONLY writes based on provided evidence. Never invent or assume information. Be factual and concise."),
        HumanMessage(content=prompt)
    ]

    response = await llm.ainvoke(messages)

    return response.content.strip()

"""
QA Validator Agent - SIMPLIFIED for 8K context models

Validates README quality, completeness, and structure.

KEY DIFFERENCE: QA Validator does NOT have file reading tools.
It receives the final_readme from state and validates it.

Follows proven pattern:
- NO file reading tools (works from final_readme input)
- Minimal prompt
- Validates output quality
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
QA_VALIDATOR_PROMPT = """You are a README Quality Validator. Validate documentation quality.

**Input:** You'll receive a generated README markdown.

**Task:** Evaluate the README on these criteria:
1. **Completeness** - Are all expected sections present? (Overview, Installation, Usage, etc.)
2. **Clarity** - Is the content clear and well-written?
3. **Structure** - Proper markdown formatting, headings hierarchy
4. **Code Examples** - Are code blocks properly formatted?
5. **Mermaid Diagrams** - If present, are they valid?

**Output:** JSON validation report:
```json
{
  "qa_score": 85,
  "qa_passed": true,
  "issues": [
    {"severity": "warning", "message": "Installation section is brief"},
    {"severity": "error", "message": "No usage examples provided"}
  ],
  "recommendations": ["Add more usage examples", "Include configuration details"]
}
```

**Tools:**
- validate_readme_structure(readme) - check structure and completeness
- validate_mermaid_diagrams(readme) - extract and validate Mermaid diagrams

**Scoring:**
- 90-100: Excellent
- 75-89: Good
- 60-74: Acceptable (needs minor improvements)
- <60: Poor (needs major improvements)

**Pass Threshold:** 60

**Limit:** 5 tool calls."""


async def run_qa_validator_agent(
    llm: BaseChatModel,
    readme_sections: dict,
    job_id: str,
    evidence_packet=None
) -> Dict[str, Any]:
    """
    Enhanced QA Validator - Validates sections with evidence-based guardrails

    Checks if expected sections are present, non-empty, AND don't contain
    forbidden phrases without evidence.

    Args:
        llm: Language model (not used in fast mode)
        readme_sections: Dict of section name -> content
        job_id: Job ID
        evidence_packet: EvidencePacket for checking forbidden phrases

    Returns:
        Results dict with success flag and validation report
    """
    try:
        import json

        # Expected sections
        EXPECTED_SECTIONS = [
            "Project Overview",
            "Features",
            "Architecture",
            "Prerequisites",
            "Quick Start Deployment",
            "Configuration",
            "Troubleshooting"
        ]

        issues = []
        score = 100
        missing_sections = []
        empty_sections = []
        forbidden_violations = []

        # Check for missing sections
        for section in EXPECTED_SECTIONS:
            if section not in readme_sections:
                missing_sections.append(section)
                issues.append({"severity": "warning", "message": f"Missing section: {section}"})
                score -= 5
            elif len(readme_sections[section].strip()) < 50:
                empty_sections.append(section)
                issues.append({"severity": "error", "message": f"Section too short or empty: {section}"})
                score -= 10

        # Check for code blocks in deployment section
        if "Quick Start Deployment" in readme_sections:
            if '```' not in readme_sections["Quick Start Deployment"]:
                issues.append({"severity": "warning", "message": "Quick Start Deployment lacks code examples"})
                score -= 5

        # Check for architecture diagram mention
        if "Architecture" in readme_sections:
            if "diagram" not in readme_sections["Architecture"].lower():
                issues.append({"severity": "info", "message": "Architecture section should mention diagram"})

        # === NEW: Evidence-Based Forbidden Phrase Checks (FIX 3 applied) ===
        if evidence_packet:
            # Combine all section content for checking
            full_content = "\n".join(readme_sections.values())

            # Define forbidden checks (removed weak port checks per FIX 3)
            forbidden_checks = [
                {
                    "phrase": "npm",
                    "evidence_required": lambda e: len(e.node_deps) > 0,
                    "message": "Claims 'npm' commands but no package.json found"
                },
                {
                    "phrase": "docker-compose",
                    "evidence_required": lambda e: e.has_docker and "docker-compose.yml" in e.docker_files,
                    "message": "Claims 'docker-compose' but no docker-compose.yml found"
                },
                {
                    "phrase": "Dockerfile",
                    "evidence_required": lambda e: e.has_docker and "Dockerfile" in e.docker_files,
                    "message": "Claims 'Dockerfile' but no Dockerfile found"
                },
                {
                    "phrase": "Whisper",
                    "evidence_required": lambda e: any("whisper" in dep.lower() for dep in e.python_deps),
                    "message": "Claims 'Whisper' without dependency evidence"
                },
                {
                    "phrase": "Keycloak",
                    "evidence_required": lambda e: any("keycloak" in dep.lower() for dep in (e.python_deps + e.node_deps)),
                    "message": "Claims 'Keycloak' without dependency evidence"
                },
                {
                    "phrase": "React",
                    "evidence_required": lambda e: "react" in [d.lower() for d in e.node_deps] or e.frontend_framework == "React",
                    "message": "Claims 'React' without evidence"
                },
                {
                    "phrase": "Vue",
                    "evidence_required": lambda e: "vue" in [d.lower() for d in e.node_deps] or e.frontend_framework == "Vue",
                    "message": "Claims 'Vue' without evidence"
                }
            ]

            # Check each forbidden phrase
            for check in forbidden_checks:
                phrase = check["phrase"]
                if phrase in full_content:
                    # Check if evidence exists
                    if not check["evidence_required"](evidence_packet):
                        forbidden_violations.append(check["message"])
                        issues.append({
                            "severity": "error",
                            "message": f"HALLUCINATION: {check['message']}"
                        })
                        score -= 15  # Heavy penalty for hallucinations

            if forbidden_violations:
                logger.warning(f"[QA] Found {len(forbidden_violations)} forbidden phrase violations")

        # Build validation report
        qa_report = {
            "qa_score": max(score, 0),  # Allow scores below 60 to show severity
            "qa_passed": score >= 60,
            "missing_sections": missing_sections,
            "empty_sections": empty_sections,
            "forbidden_violations": forbidden_violations,
            "issues": issues,
            "recommendations": [] if score >= 90 else [
                "Ensure all sections have meaningful content",
                "Add code examples to deployment instructions",
                "Remove hallucinated commands/technologies without evidence"
            ]
        }

        output_json = json.dumps(qa_report, indent=2)

        # Note: QA Validator doesn't use LangGraph messages, so metrics will be empty
        # But we include the call for consistency with other agents
        metrics = extract_agent_metrics([])

        return {
            "success": True,
            "output": output_json,
            "agent": "QAValidator",
            **metrics
        }

    except Exception as e:
        logger.error(f"QAValidator failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "agent": "QAValidator"
        }

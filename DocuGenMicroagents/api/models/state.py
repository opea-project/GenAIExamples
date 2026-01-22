"""
LangGraph State Definition for DocuGen Micro-Agents
Enhanced with agent messaging, evidence packs, and metrics tracking
"""

from typing import TypedDict, Dict, List, Any, Optional
from models.evidence import EvidencePacket


class DocGenState(TypedDict):
    """
    Shared state for the micro-agent documentation generation workflow.
    Each agent reads from and writes to this state.
    """

    # Job Information
    job_id: str
    repo_url: str

    # Repository Data (populated by clone step)
    repo_path: Optional[str]
    repo_name: Optional[str]
    default_branch: Optional[str]
    is_subfolder_target: Optional[bool]

    # Project Detection (populated by project detector)
    is_monorepo: Optional[bool]
    detected_projects: Optional[List[Dict[str, Any]]]
    skipped_folders: Optional[List[Dict[str, Any]]]
    selected_projects: Optional[List[str]]
    awaiting_project_selection: Optional[bool]

    # Evidence-Based Architecture
    evidence_packet: Optional[EvidencePacket]  # Central evidence store

    # Analysis Agent Outputs
    file_structure: Optional[str]
    languages: Optional[Dict[str, int]]
    key_files: Optional[List[str]]
    code_summary: Optional[str]

    # Dependency Analysis (NEW - from DependencyAnalyzer)
    dependency_report: Optional[Dict[str, Any]]  # Full dependency analysis
    security_warnings: Optional[List[Dict[str, str]]]  # Vulnerability warnings

    # Environment Config (NEW - from EnvConfigParser)
    env_variables: Optional[List[Dict[str, Any]]]  # Extracted env vars
    config_files_found: Optional[List[str]]

    # Code Analysis Agent Outputs
    # API Reference (NEW - from APIReferenceAgent)
    api_endpoints: Optional[List[Dict[str, Any]]]  # Detected endpoints
    api_documentation: Optional[str]

    # Call Graph (NEW - from CallGraphAgent)
    call_graph: Optional[Dict[str, Any]]  # Function call relationships

    # Error Analysis (NEW - from ErrorAnalysisAgent)
    error_handlers: Optional[List[Dict[str, Any]]]  # Exception handlers found
    error_analysis: Optional[Dict[str, Any]]

    # Planning
    project_type: Optional[str]
    documentation_sections: Optional[List[str]]
    section_instructions: Optional[Dict[str, str]]

    # Content Generation
    readme_sections: Optional[Dict[str, str]]

    # Visualization
    mermaid_diagrams: Optional[Dict[str, str]]

    # Quality Assurance
    qa_validation_result: Optional[Dict[str, Any]]  # QA validator output
    qa_score: Optional[int]
    qa_passed: Optional[bool]

    # Final Output
    final_readme: Optional[str]

    # Agent-to-Agent Communication (NEW)
    agent_messages: Optional[List[Dict[str, Any]]]  # Messages between agents
    # Format: [{"from": "APIReference", "to": "Mermaid", "type": "data", "content": {...}}]

    # Performance Metrics (NEW)
    agent_metrics: Optional[Dict[str, Dict[str, Any]]]  # Per-agent metrics
    blast_radius_report: Optional[Dict[str, Any]]  # Blast radius calculation
    total_tokens_used: Optional[int]
    total_duration_ms: Optional[float]

    # Error Handling
    error: Optional[str]
    retry_count: int
    failed_agents: Optional[List[str]]  # List of agents that failed

    # Metadata
    workflow_status: str  # pending, in_progress, completed, failed
    current_agent: Optional[str]

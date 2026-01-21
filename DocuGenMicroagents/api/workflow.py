"""
Simplified LangGraph Workflow for 10 Micro-Agents
Optimized for 8K context models with evidence-based architecture
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from models.state import DocGenState
from models.evidence import EvidencePacket, EvidenceItem
from models import get_log_manager, LogType
from services import get_llm, GitService
from services.git_service import parse_github_url
from utils import detect_projects
from config import settings
from langchain_core.messages import AIMessage
import os
import json
import re

# Import all agents (6 section writers + planner + mermaid + QA)
from agents.code_explorer_agent import run_code_explorer_agent
from agents.api_reference_agent import run_api_reference_agent
from agents.call_graph_agent import run_call_graph_agent
from agents.error_analysis_agent import run_error_analysis_agent
from agents.env_config_agent import run_env_config_agent
from agents.dependency_analyzer_agent import run_dependency_analyzer_agent
from agents.planner_agent import run_planner_agent
from agents.mermaid_agent import run_mermaid_agent
from agents.qa_validator_agent import run_qa_validator_agent
from core.metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class SimplifiedDocuGenWorkflow:
    """
    Simplified workflow with 9 micro-agents optimized for 8K context models.

    Architecture:
    - 6 Section Writer Agents (write sections directly)
      - Code Explorer: Project Overview + Features
      - API Reference: API Reference
      - Call Graph: Architecture
      - Error Analysis: Troubleshooting
      - Env Config: Configuration
      - Dependency Analyzer: Prerequisites + Quick Start Deployment
    - 1 Planner Agent (decides which sections to include)
    - 1 Mermaid Agent (generates architecture diagram)
    - 1 QA Agent (validates quality)
    """

    def __init__(self):
        self.git_service = GitService()
        self.log_manager = get_log_manager()
        self.graph = None
        self.checkpointer = None
        self.metrics_collectors = {}  # Store metrics collector per job_id

    def _get_metrics_collector(self, job_id: str) -> MetricsCollector:
        """Get or create metrics collector for a job"""
        if job_id not in self.metrics_collectors:
            self.metrics_collectors[job_id] = MetricsCollector(job_id)
        return self.metrics_collectors[job_id]

    def _get_target_path(self, state: DocGenState) -> str:
        """
        Get the target path for agent analysis.
        If user selected specific projects, return path to that project.
        Otherwise, return full repo path.
        """
        repo_path = state["repo_path"]
        selected_projects = state.get("selected_projects")

        if selected_projects and len(selected_projects) > 0:
            import os
            return os.path.join(repo_path, selected_projects[0])
        return repo_path

    def _get_final_assistant_text(self, messages) -> str:
        """
        Extract the last non-empty AIMessage content from LangGraph result.

        FIX: messages[-1] is not guaranteed to be the final assistant answer.
        It can be a ToolMessage, intermediate AIMessage, or truncated stub.
        """
        # Walk backwards and return the last assistant AIMessage with non-empty content
        for m in reversed(messages or []):
            if isinstance(m, AIMessage) and isinstance(getattr(m, "content", None), str):
                txt = m.content.strip()
                if txt:
                    return txt
        # Fallback
        return (messages[-1].content or "").strip() if messages else ""

    def _store_section(self, sections_dict: Dict[str, str], heading: str, section_md: str):
        """
        Store section with guard against overwriting good content with stubs.

        FIX: Don't replace a complete section with an empty header-only stub.
        """
        new_md = (section_md or "").strip()
        old_md = (sections_dict.get(heading) or "").strip()

        # Don't overwrite a real section (>= 80 chars) with a stub (< 80 chars)
        if len(new_md) < 80 and len(old_md) >= 80:
            logger.warning(f"[Parser] Skipping stub overwrite for '{heading}': {len(new_md)} < {len(old_md)} chars")
            return

        sections_dict[heading] = new_md

    def _parse_and_store_sections(self, output: str, sections_dict: Dict[str, str]):
        """
        Parse agent output to extract markdown sections with subsection handling.

        FIX: Merges ### subsections back into their parent ## sections.

        Logic:
        - If we see "## Parent" followed by "### Child", merge them into one section
        - If we see standalone "## Section" with content, store it as-is
        """
        # Split by ## headings but preserve them
        lines = output.split('\n')
        current_section = None
        current_content = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if this is a ## heading
            if line.startswith('## '):
                # Store previous section if exists
                if current_section and current_content:
                    full_content = '\n'.join(current_content).strip()
                    self._store_section(sections_dict, current_section, full_content)

                # Start new section
                current_section = line.replace('##', '').strip()
                current_content = [line]  # Include the heading itself

            elif line.strip():  # Non-empty line
                if current_section:
                    current_content.append(line)
            else:  # Empty line
                if current_section:
                    current_content.append(line)

            i += 1

        # Store last section
        if current_section and current_content:
            full_content = '\n'.join(current_content).strip()
            self._store_section(sections_dict, current_section, full_content)

    async def create_workflow(self) -> StateGraph:
        """Build the simplified 10-agent workflow"""
        workflow = StateGraph(DocGenState)

        # Add nodes
        workflow.add_node("clone_repository", self.clone_repository_node)
        workflow.add_node("project_detection", self.project_detection_node)

        # Section Writer Agents
        workflow.add_node("code_explorer", self.code_explorer_node)
        workflow.add_node("api_reference", self.api_reference_node)
        workflow.add_node("call_graph", self.call_graph_node)
        workflow.add_node("error_analysis", self.error_analysis_node)
        workflow.add_node("env_config", self.env_config_node)
        workflow.add_node("dependency_analyzer", self.dependency_analyzer_node)

        # Evidence Aggregation
        workflow.add_node("evidence_aggregator", self.evidence_aggregator_node)

        # Planning
        workflow.add_node("planner", self.planner_node)

        # Mermaid Diagram Generation
        workflow.add_node("mermaid", self.mermaid_node)

        # QA Validation
        workflow.add_node("qa_validator", self.qa_validator_node)

        # Final assembly
        workflow.add_node("assembly", self.assembly_node)

        # Define workflow flow (NEW: analysis → evidence_aggregator → planner → mermaid → QA → assembly)
        workflow.set_entry_point("clone_repository")
        workflow.add_edge("clone_repository", "project_detection")
        workflow.add_edge("project_detection", "code_explorer")
        workflow.add_edge("code_explorer", "api_reference")
        workflow.add_edge("api_reference", "call_graph")
        workflow.add_edge("call_graph", "error_analysis")
        workflow.add_edge("error_analysis", "env_config")
        workflow.add_edge("env_config", "dependency_analyzer")
        workflow.add_edge("dependency_analyzer", "evidence_aggregator")  # NEW: aggregate evidence after all analysis
        workflow.add_edge("evidence_aggregator", "planner")  # Planner uses evidence for routing
        workflow.add_edge("planner", "mermaid")
        workflow.add_edge("mermaid", "qa_validator")
        workflow.add_edge("qa_validator", "assembly")
        workflow.add_edge("assembly", END)

        # Use memory checkpointer (ephemeral)
        checkpointer = MemorySaver()
        compiled = workflow.compile(checkpointer=checkpointer)

        self.graph = compiled
        self.checkpointer = checkpointer
        return compiled

    async def clone_repository_node(self, state: DocGenState) -> DocGenState:
        """Clone the GitHub repository (reuse existing implementation)"""
        job_id = state["job_id"]
        repo_url = state["repo_url"]

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message=f"📦 Cloning repository: {repo_url}"
        )

        try:
            parsed_url = parse_github_url(repo_url)

            def progress_callback(message: str):
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.log_manager.log_async(
                        job_id=job_id,
                        log_type=LogType.INFO,
                        message=message
                    ))
                except RuntimeError:
                    logger.info(message)

            repo_path, metadata = self.git_service.clone_repository(
                parsed_url["clone_url"],
                branch=parsed_url["branch"],
                progress_callback=progress_callback
            )

            if parsed_url["is_subfolder"]:
                import os
                target_path = os.path.join(repo_path, parsed_url["subfolder"])
                if not os.path.exists(target_path):
                    raise ValueError(f"Subfolder '{parsed_url['subfolder']}' not found")
                state["repo_path"] = target_path
                state["repo_name"] = parsed_url["display_name"]
                state["is_subfolder_target"] = True
            else:
                state["repo_path"] = repo_path
                state["repo_name"] = parsed_url["repo"]
                state["is_subfolder_target"] = False

            state["default_branch"] = metadata["default_branch"]
            state["workflow_status"] = "detecting"

            await self.log_manager.log_async(
                job_id=job_id,
                log_type=LogType.SUCCESS,
                message="✅ Repository cloned successfully"
            )

            return state

        except Exception as e:
            logger.error(f"Clone failed: {e}")
            await self.log_manager.log_async(
                job_id=job_id,
                log_type=LogType.ERROR,
                message=f"❌ Clone failed: {str(e)}"
            )
            state["error"] = str(e)
            state["workflow_status"] = "failed"
            raise

    async def project_detection_node(self, state: DocGenState) -> DocGenState:
        """Detect projects in repository (reuse existing implementation)"""
        job_id = state["job_id"]
        repo_path = state["repo_path"]
        is_subfolder = state.get("is_subfolder_target", False)

        if is_subfolder:
            await self.log_manager.log_async(
                job_id=job_id,
                log_type=LogType.SUCCESS,
                message=f"🎯 Targeting subfolder: {state['repo_name']}"
            )
            state["awaiting_project_selection"] = False
            state["selected_projects"] = None
            state["is_monorepo"] = False
            state["detected_projects"] = []
            state["workflow_status"] = "analyzing"
            return state

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message="🔍 Detecting projects..."
        )

        try:
            detection_result = detect_projects(repo_path)
            state["is_monorepo"] = detection_result["is_monorepo"]
            state["detected_projects"] = detection_result["projects"]
            state["skipped_folders"] = detection_result.get("skipped_folders", [])

            if detection_result["project_count"] <= 1:
                state["awaiting_project_selection"] = False
                state["selected_projects"] = None
                state["workflow_status"] = "analyzing"
            else:
                # Multiple projects - need selection (handled by server)
                state["awaiting_project_selection"] = True
                state["workflow_status"] = "awaiting_selection"

            return state

        except Exception as e:
            logger.error(f"Detection failed: {e}")
            state["awaiting_project_selection"] = False
            state["selected_projects"] = None
            state["workflow_status"] = "analyzing"
            return state

    # Section Writer Agents
    async def code_explorer_node(self, state: DocGenState) -> DocGenState:
        """Run Code Explorer agent - writes Overview + Features sections"""
        job_id = state["job_id"]
        target_path = self._get_target_path(state)

        # Start metrics tracking
        metrics = self._get_metrics_collector(job_id)
        metrics.start_agent("CodeExplorer")

        # CRITICAL: Update repo_name to selected project name if project was selected
        selected_projects = state.get("selected_projects")
        if selected_projects and len(selected_projects) > 0:
            # Update repo_name to the selected project folder name
            state["repo_name"] = selected_projects[0]
            logger.info(f"[CodeExplorer] Updated repo_name to selected project: {state['repo_name']}")

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message=f"🔍 Running Overview & Features Writer (1/7) for {state['repo_name']}...",
            agent_name="CodeExplorer"
        )

        llm = get_llm(model_name=settings.CODE_EXPLORER_MODEL, temperature=0.7)
        result = await run_code_explorer_agent(llm=llm, repo_path=target_path, job_id=job_id)

        if result.get("success"):
            # Parse output to extract two sections: Project Overview and Features
            output = result.get("output", "")
            sections_dict = state.get("readme_sections") or {}

            # Extract sections from output (they're in format: ## Section Name\n\nContent...)
            self._parse_and_store_sections(output, sections_dict)
            state["readme_sections"] = sections_dict

            logger.info(f"[CodeExplorer] Stored sections: {list(sections_dict.keys())}")
            await self.log_manager.log_async(
                job_id=job_id,
                log_type=LogType.SUCCESS,
                message="✅ Overview & Features sections completed",
                agent_name="CodeExplorer"
            )

            # End metrics tracking (success)
            metrics.end_agent(
                "CodeExplorer",
                success=True,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                tool_calls=result.get("tool_calls", 0),
                llm_calls=result.get("llm_calls", 0)
            )
        else:
            logger.error(f"CodeExplorer failed: {result.get('error')}")
            # End metrics tracking (failure)
            metrics.end_agent("CodeExplorer", success=False, error_message=result.get('error'))

        state["current_agent"] = "CodeExplorer"
        return state

    async def api_reference_node(self, state: DocGenState) -> DocGenState:
        """Run API Reference agent - extracts endpoint data (no markdown sections)"""
        job_id = state["job_id"]
        target_path = self._get_target_path(state)

        # Start metrics tracking
        metrics = self._get_metrics_collector(job_id)
        metrics.start_agent("APIReference")

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message="📡 Running API Endpoint Extractor (2/7)...",
            agent_name="APIReference"
        )

        llm = get_llm(model_name=settings.API_REFERENCE_MODEL, temperature=0.7)
        result = await run_api_reference_agent(llm=llm, repo_path=target_path, job_id=job_id)

        if result.get("success"):
            output = result.get("output", "")
            # Parse JSON output to extract endpoint data
            import json
            import re
            try:
                # Try to find JSON in output (might be wrapped in markdown code block)
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Try to find raw JSON object
                    json_match = re.search(r'\{.*\}', output, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        json_str = output

                endpoint_data = json.loads(json_str)
                state["api_endpoints"] = endpoint_data.get("endpoints", [])
                logger.info(f"[APIReference] Extracted {len(state['api_endpoints'])} endpoints")

                await self.log_manager.log_async(
                    job_id=job_id,
                    log_type=LogType.SUCCESS,
                    message=f"✅ Extracted {len(state['api_endpoints'])} API endpoints",
                    agent_name="APIReference"
                )
                # End metrics tracking (success)
                metrics.end_agent(
                    "APIReference",
                    success=True,
                    input_tokens=result.get("input_tokens", 0),
                    output_tokens=result.get("output_tokens", 0),
                    tool_calls=result.get("tool_calls", 0),
                    llm_calls=result.get("llm_calls", 0)
                )
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"[APIReference] Failed to parse JSON: {e}. Storing empty endpoint list.")
                state["api_endpoints"] = []
                await self.log_manager.log_async(
                    job_id=job_id,
                    log_type=LogType.WARNING,
                    message="⚠️ No API endpoints extracted",
                    agent_name="APIReference"
                )
                # End metrics tracking (success with warning)
                metrics.end_agent(
                    "APIReference",
                    success=True,
                    input_tokens=result.get("input_tokens", 0),
                    output_tokens=result.get("output_tokens", 0),
                    tool_calls=result.get("tool_calls", 0),
                    llm_calls=result.get("llm_calls", 0)
                )
        else:
            logger.error(f"APIReference failed: {result.get('error')}")
            # End metrics tracking (failure)
            metrics.end_agent("APIReference", success=False, error_message=result.get('error'))

        state["current_agent"] = "APIReference"
        return state

    async def call_graph_node(self, state: DocGenState) -> DocGenState:
        """Run Call Graph agent - writes Architecture section"""
        job_id = state["job_id"]
        target_path = self._get_target_path(state)

        # Start metrics tracking
        metrics = self._get_metrics_collector(job_id)
        metrics.start_agent("CallGraph")

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message="🔗 Running Architecture Writer (3/7)...",
            agent_name="CallGraph"
        )

        llm = get_llm(model_name=settings.CALL_GRAPH_MODEL, temperature=0.7)
        result = await run_call_graph_agent(llm=llm, repo_path=target_path, job_id=job_id)

        if result.get("success"):
            output = result.get("output", "")
            sections_dict = state.get("readme_sections") or {}
            self._parse_and_store_sections(output, sections_dict)
            state["readme_sections"] = sections_dict

            logger.info(f"[CallGraph] Stored sections: {list(sections_dict.keys())}")
            await self.log_manager.log_async(
                job_id=job_id,
                log_type=LogType.SUCCESS,
                message="✅ Architecture section completed",
                agent_name="CallGraph"
            )
            # End metrics tracking (success)
            metrics.end_agent(
                "CallGraph",
                success=True,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                tool_calls=result.get("tool_calls", 0),
                llm_calls=result.get("llm_calls", 0)
            )
        else:
            logger.error(f"CallGraph failed: {result.get('error')}")
            # End metrics tracking (failure)
            metrics.end_agent("CallGraph", success=False, error_message=result.get('error'))

        state["current_agent"] = "CallGraph"
        return state

    async def error_analysis_node(self, state: DocGenState) -> DocGenState:
        """Run Error Analysis agent - writes Troubleshooting section"""
        job_id = state["job_id"]
        target_path = self._get_target_path(state)

        # Start metrics tracking
        metrics = self._get_metrics_collector(job_id)
        metrics.start_agent("ErrorAnalysis")

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message="⚠️ Running Troubleshooting Writer (4/7)...",
            agent_name="ErrorAnalysis"
        )

        llm = get_llm(model_name=settings.ERROR_ANALYSIS_MODEL, temperature=0.7)
        result = await run_error_analysis_agent(llm=llm, repo_path=target_path, job_id=job_id)

        if result.get("success"):
            output = result.get("output", "")
            sections_dict = state.get("readme_sections") or {}
            self._parse_and_store_sections(output, sections_dict)
            state["readme_sections"] = sections_dict

            logger.info(f"[ErrorAnalysis] Stored sections: {list(sections_dict.keys())}")
            await self.log_manager.log_async(
                job_id=job_id,
                log_type=LogType.SUCCESS,
                message="✅ Troubleshooting section completed",
                agent_name="ErrorAnalysis"
            )
            # End metrics tracking (success)
            metrics.end_agent(
                "ErrorAnalysis",
                success=True,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                tool_calls=result.get("tool_calls", 0),
                llm_calls=result.get("llm_calls", 0)
            )
        else:
            logger.error(f"ErrorAnalysis failed: {result.get('error')}")
            # End metrics tracking (failure)
            metrics.end_agent("ErrorAnalysis", success=False, error_message=result.get('error'))

        state["current_agent"] = "ErrorAnalysis"
        return state

    async def env_config_node(self, state: DocGenState) -> DocGenState:
        """Run Environment Config agent - writes Configuration section"""
        job_id = state["job_id"]
        target_path = self._get_target_path(state)

        # Start metrics tracking
        metrics = self._get_metrics_collector(job_id)
        metrics.start_agent("EnvConfig")

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message="⚙️ Running Configuration Writer (5/7)...",
            agent_name="EnvConfig"
        )

        llm = get_llm(model_name=settings.ENV_CONFIG_MODEL, temperature=0.7)
        result = await run_env_config_agent(llm=llm, repo_path=target_path, job_id=job_id)

        if result.get("success"):
            output = result.get("output", "")

            # DEBUG: Log raw output
            logger.info(f"[EnvConfig] raw_output_head={output[:400]!r}")
            logger.info(f"[EnvConfig] raw_output_tail={output[-400:]!r}")

            sections_dict = state.get("readme_sections") or {}
            self._parse_and_store_sections(output, sections_dict)
            state["readme_sections"] = sections_dict

            logger.info(f"[EnvConfig] Stored sections: {list(sections_dict.keys())}")
            await self.log_manager.log_async(
                job_id=job_id,
                log_type=LogType.SUCCESS,
                message="✅ Configuration section completed",
                agent_name="EnvConfig"
            )
            # End metrics tracking (success)
            metrics.end_agent(
                "EnvConfig",
                success=True,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                tool_calls=result.get("tool_calls", 0),
                llm_calls=result.get("llm_calls", 0)
            )
        else:
            logger.error(f"EnvConfig failed: {result.get('error')}")
            # End metrics tracking (failure)
            metrics.end_agent("EnvConfig", success=False, error_message=result.get('error'))

        state["current_agent"] = "EnvConfig"
        return state

    async def dependency_analyzer_node(self, state: DocGenState) -> DocGenState:
        """Run Dependency Analyzer agent - writes Prerequisites & Deployment sections"""
        job_id = state["job_id"]
        target_path = self._get_target_path(state)

        # Start metrics tracking
        metrics = self._get_metrics_collector(job_id)
        metrics.start_agent("DependencyAnalyzer")

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message="📦 Running Prerequisites & Deployment Writer (6/7)...",
            agent_name="DependencyAnalyzer"
        )

        llm = get_llm(model_name=settings.DEPENDENCY_ANALYZER_MODEL, temperature=0.7)
        repo_url = state.get("repo_url", "")
        result = await run_dependency_analyzer_agent(llm=llm, repo_path=target_path, job_id=job_id, repo_url=repo_url)

        if result.get("success"):
            output = result.get("output", "")

            # DEBUG: Log raw output
            logger.info(f"[DependencyAnalyzer] raw_output_head={output[:400]!r}")
            logger.info(f"[DependencyAnalyzer] raw_output_tail={output[-400:]!r}")

            sections_dict = state.get("readme_sections") or {}
            self._parse_and_store_sections(output, sections_dict)
            state["readme_sections"] = sections_dict

            logger.info(f"[DependencyAnalyzer] Stored sections: {list(sections_dict.keys())}")
            await self.log_manager.log_async(
                job_id=job_id,
                log_type=LogType.SUCCESS,
                message="✅ Prerequisites & Deployment sections completed",
                agent_name="DependencyAnalyzer"
            )
            # End metrics tracking (success)
            metrics.end_agent(
                "DependencyAnalyzer",
                success=True,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                tool_calls=result.get("tool_calls", 0),
                llm_calls=result.get("llm_calls", 0)
            )
        else:
            logger.error(f"DependencyAnalyzer failed: {result.get('error')}")
            # End metrics tracking (failure)
            metrics.end_agent("DependencyAnalyzer", success=False, error_message=result.get('error'))

        state["current_agent"] = "DependencyAnalyzer"
        return state

    # Evidence Aggregation
    async def evidence_aggregator_node(self, state: DocGenState) -> DocGenState:
        """
        DUAL-MODE Evidence Aggregator - Collects evidence from file system and agent outputs.

        This node creates the central EvidencePacket by:
        1. Direct file system checks (requirements.txt, package.json, etc.)
        2. Extracting structured data from agent outputs (dual-mode: supports both strings and JSON)

        FIX 1: Dual-mode aggregator - works with current string outputs AND future JSON outputs
        FIX 2: Deterministic repo_name derivation from URL or folder path
        FIX: Uses target_path (selected project) instead of repo_path (root)
        """
        job_id = state["job_id"]
        repo_url = state.get("repo_url", "")
        readme_sections = state.get("readme_sections", {})

        # CRITICAL: Use target path (respects project selection)
        target_path = self._get_target_path(state)

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message="📊 Aggregating evidence from repository...",
            agent_name="EvidenceAggregator"
        )

        try:
            # FIX 2: Derive repo_name deterministically (never from LLM output)
            # Use selected project name if available, otherwise derive from URL/path
            selected_projects = state.get("selected_projects")
            if selected_projects and len(selected_projects) > 0:
                repo_name = selected_projects[0]
            elif repo_url:
                # Parse from GitHub URL: github.com/user/repo-name
                match = re.search(r'github\.com/[^/]+/([^/\.]+)', repo_url)
                repo_name = match.group(1) if match else os.path.basename(target_path)
            else:
                # Use folder name
                repo_name = os.path.basename(target_path) if target_path else "Repository"

            # Initialize evidence packet with target_path
            evidence = EvidencePacket(repo_name=repo_name, repo_path=target_path)

            # === DIRECT FILE SYSTEM CHECKS (don't rely on agent outputs) ===

            # Check for Python dependencies (root and subdirectories)
            python_dep_locations = [
                os.path.join(target_path, "requirements.txt"),
                os.path.join(target_path, "api", "requirements.txt"),
                os.path.join(target_path, "backend", "requirements.txt"),
                os.path.join(target_path, "server", "requirements.txt")
            ]

            for requirements_path in python_dep_locations:
                if os.path.exists(requirements_path):
                    rel_path = os.path.relpath(requirements_path, target_path)
                    evidence.add_evidence(EvidenceItem(
                        category="dependency",
                        key=rel_path,
                        value="Python dependencies",
                        source_files=[rel_path]
                    ))
                    try:
                        with open(requirements_path, 'r', encoding='utf-8', errors='ignore') as f:
                            deps = [
                                line.split('==')[0].split('>=')[0].split('~=')[0].strip()
                                for line in f
                                if line.strip() and not line.startswith('#')
                            ]
                            evidence.python_deps.extend(deps)
                            logger.info(f"[Evidence] Found {len(deps)} Python dependencies in {rel_path}")
                    except Exception as e:
                        logger.warning(f"[Evidence] Failed to parse {rel_path}: {e}")

            if evidence.python_deps:
                evidence.has_backend = True
                # Remove duplicates
                evidence.python_deps = list(set(evidence.python_deps))

            # Check for Node.js dependencies (root and subdirectories)
            node_dep_locations = [
                os.path.join(target_path, "package.json"),
                os.path.join(target_path, "ui", "package.json"),
                os.path.join(target_path, "frontend", "package.json"),
                os.path.join(target_path, "client", "package.json")
            ]

            for package_json_path in node_dep_locations:
                if os.path.exists(package_json_path):
                    rel_path = os.path.relpath(package_json_path, target_path)
                    evidence.has_frontend = True
                    try:
                        with open(package_json_path, 'r', encoding='utf-8') as f:
                            pkg = json.load(f)
                            deps = list(pkg.get("dependencies", {}).keys())
                            evidence.node_deps.extend(deps)

                            # Detect frontend framework
                            if "react" in deps and not evidence.frontend_framework:
                                evidence.frontend_framework = "React"
                            elif "vue" in deps and not evidence.frontend_framework:
                                evidence.frontend_framework = "Vue"
                            elif "@angular/core" in deps and not evidence.frontend_framework:
                                evidence.frontend_framework = "Angular"

                            evidence.add_evidence(EvidenceItem(
                                category="dependency",
                                key=rel_path,
                                value=f"Node.js project with {len(deps)} dependencies",
                                source_files=[rel_path]
                            ))
                            logger.info(f"[Evidence] Found {len(deps)} Node dependencies in {rel_path}")
                    except Exception as e:
                        logger.warning(f"[Evidence] Failed to parse {rel_path}: {e}")

            if evidence.node_deps:
                # Remove duplicates
                evidence.node_deps = list(set(evidence.node_deps))

            # Check for Docker
            dockerfile_path = os.path.join(target_path, "Dockerfile")
            compose_path = os.path.join(target_path, "docker-compose.yml")
            if os.path.exists(dockerfile_path):
                evidence.has_docker = True
                evidence.docker_files.append("Dockerfile")
                evidence.add_evidence(EvidenceItem(
                    category="infrastructure",
                    key="Dockerfile",
                    value="Docker containerization",
                    source_files=["Dockerfile"]
                ))
            if os.path.exists(compose_path):
                evidence.has_docker = True
                evidence.docker_files.append("docker-compose.yml")
                evidence.add_evidence(EvidenceItem(
                    category="infrastructure",
                    key="docker-compose.yml",
                    value="Docker Compose orchestration",
                    source_files=["docker-compose.yml"]
                ))

            if evidence.has_docker:
                logger.info(f"[Evidence] Found Docker files: {evidence.docker_files}")

            # Check for .env files
            env_example_path = os.path.join(target_path, ".env.example")
            if os.path.exists(env_example_path):
                evidence.env_files.append(".env.example")
                evidence.add_evidence(EvidenceItem(
                    category="config",
                    key=".env.example",
                    value="Environment configuration template",
                    source_files=[".env.example"]
                ))
                logger.info("[Evidence] Found .env.example")

            # Extract API endpoints from state (populated by API Reference agent)
            api_endpoints = state.get("api_endpoints", [])
            if api_endpoints:
                evidence.api_endpoints = api_endpoints
                logger.info(f"[Evidence] Extracted {len(api_endpoints)} API endpoints from state")

            # Detect languages from file extensions
            try:
                for root, dirs, files in os.walk(target_path):
                    # Skip node_modules, .git, venv, etc.
                    dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'venv', '__pycache__', 'dist', 'build']]

                    for file in files:
                        ext = os.path.splitext(file)[1]
                        if ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rs', '.cpp', '.c', '.rb']:
                            lang_map = {
                                '.py': 'Python', '.js': 'JavaScript', '.jsx': 'JavaScript',
                                '.ts': 'TypeScript', '.tsx': 'TypeScript', '.java': 'Java',
                                '.go': 'Go', '.rs': 'Rust', '.cpp': 'C++', '.c': 'C', '.rb': 'Ruby'
                            }
                            lang = lang_map.get(ext, 'Unknown')
                            evidence.languages[lang] = evidence.languages.get(lang, 0) + 1

                logger.info(f"[Evidence] Detected languages: {evidence.languages}")
            except Exception as e:
                logger.warning(f"[Evidence] Failed to detect languages: {e}")

            # Store evidence packet in state
            state["evidence_packet"] = evidence

            await self.log_manager.log_async(
                job_id=job_id,
                log_type=LogType.SUCCESS,
                message=f"✅ Evidence aggregated: {len(evidence.python_deps)} Python deps, {len(evidence.node_deps)} Node deps, {len(evidence.docker_files)} Docker files",
                agent_name="EvidenceAggregator"
            )

            logger.info(f"[Evidence] Final evidence: {evidence.to_dict()}")

        except Exception as e:
            logger.error(f"Evidence aggregation failed: {e}")
            # Create minimal evidence packet on failure
            state["evidence_packet"] = EvidencePacket(
                repo_name=os.path.basename(target_path) if target_path else "Repository",
                repo_path=target_path
            )
            await self.log_manager.log_async(
                job_id=job_id,
                log_type=LogType.WARNING,
                message=f"⚠️ Evidence aggregation failed, using minimal evidence: {str(e)}",
                agent_name="EvidenceAggregator"
            )

        state["current_agent"] = "EvidenceAggregator"
        return state

    # Planning
    async def planner_node(self, state: DocGenState) -> DocGenState:
        """Run Planner agent - decides which sections to include"""
        job_id = state["job_id"]
        target_path = self._get_target_path(state)

        # Start metrics tracking
        metrics = self._get_metrics_collector(job_id)
        metrics.start_agent("Planner")

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message="📋 Running Planner (7/7)...",
            agent_name="Planner"
        )

        llm = get_llm(model_name=settings.PLANNER_MODEL, temperature=0.7)
        result = await run_planner_agent(llm=llm, repo_path=target_path, job_id=job_id)

        if result.get("success"):
            output = result.get("output", "")
            # Try to parse JSON output
            import json
            try:
                plan_data = json.loads(output)
                state["project_type"] = plan_data.get("project_type", "Unknown")
                state["documentation_sections"] = plan_data.get("sections", ["Project Overview", "Features", "Architecture", "Prerequisites", "Quick Start Deployment", "Troubleshooting"])
                logger.info(f"[Planner] Planned sections: {state['documentation_sections']}")
            except:
                state["project_type"] = "Unknown"
                state["documentation_sections"] = ["Project Overview", "Features", "Architecture", "Prerequisites", "Quick Start Deployment", "Troubleshooting"]

            await self.log_manager.log_async(
                job_id=job_id,
                log_type=LogType.SUCCESS,
                message=f"✅ Planner completed - {len(state['documentation_sections'])} sections planned",
                agent_name="Planner"
            )
            # End metrics tracking (success)
            metrics.end_agent(
                "Planner",
                success=True,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                tool_calls=result.get("tool_calls", 0),
                llm_calls=result.get("llm_calls", 0)
            )
        else:
            logger.error(f"Planner failed: {result.get('error')}")
            # End metrics tracking (failure)
            metrics.end_agent("Planner", success=False, error_message=result.get('error'))

        state["current_agent"] = "Planner"
        return state

    async def mermaid_node(self, state: DocGenState) -> DocGenState:
        """Run Mermaid Diagram agent - generates architecture diagram with semantic validation"""
        job_id = state["job_id"]
        target_path = self._get_target_path(state)
        evidence_packet = state.get("evidence_packet")

        # Start metrics tracking
        metrics = self._get_metrics_collector(job_id)
        metrics.start_agent("Mermaid")

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message="📊 Generating architecture diagram...",
            agent_name="Mermaid"
        )

        llm = get_llm(model_name=settings.MERMAID_MODEL, temperature=0.7)
        # Pass API endpoints from state to Mermaid agent
        api_endpoints = state.get("api_endpoints", [])
        result = await run_mermaid_agent(llm=llm, repo_path=target_path, job_id=job_id, api_endpoints=api_endpoints)

        if result.get("success"):
            diagram_output = result.get("output", "")
            # Extract only the mermaid code (remove markdown blocks and extra text)
            diagram_code = self._extract_mermaid_code(diagram_output)
            if diagram_code:
                # === NEW: Semantic Validation (FIX 4 applied) ===
                is_valid, errors = self._validate_mermaid_semantics(diagram_code, evidence_packet)

                if not is_valid:
                    logger.warning(f"[Mermaid] Semantic validation failed: {errors}")
                    await self.log_manager.log_async(
                        job_id=job_id,
                        log_type=LogType.WARNING,
                        message=f"⚠️ Diagram has semantic issues: {', '.join(errors[:2])}",
                        agent_name="Mermaid"
                    )
                    # Note: We still use the diagram, but log the issues
                    # Future enhancement: add a retry mechanism here

                state["mermaid_diagrams"] = {"architecture": diagram_code}
                logger.info(f"[Mermaid] Extracted diagram: {len(diagram_code)} chars")
            else:
                state["mermaid_diagrams"] = {}
                logger.warning("[Mermaid] Could not extract valid mermaid code")

            await self.log_manager.log_async(
                job_id=job_id,
                log_type=LogType.SUCCESS,
                message="✅ Mermaid Generator completed",
                agent_name="Mermaid"
            )
            # End metrics tracking (success)
            metrics.end_agent(
                "Mermaid",
                success=True,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                tool_calls=result.get("tool_calls", 0),
                llm_calls=result.get("llm_calls", 0)
            )
        else:
            logger.error(f"Mermaid failed: {result.get('error')}")
            # End metrics tracking (failure)
            metrics.end_agent("Mermaid", success=False, error_message=result.get('error'))

        state["current_agent"] = "Mermaid"
        return state

    def _extract_mermaid_code(self, text: str) -> str:
        """Extract clean mermaid code from agent output"""
        # Try to find mermaid code block
        patterns = [
            r'```mermaid\s+(.*?)\s+```',  # ```mermaid ... ```
            r'```\s+(graph\s+TD.*?)```',   # ``` graph TD ... ```
            r'(graph\s+TD.*?)(?=\n\n|\Z)'  # graph TD ... (until double newline or end)
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                code = match.group(1).strip()
                # Validate it starts with graph/flowchart
                if code.startswith(('graph ', 'flowchart ', 'sequenceDiagram', 'classDiagram')):
                    return code

        # Fallback: if text starts with graph/flowchart directly
        if text.strip().startswith(('graph ', 'flowchart ')):
            return text.strip()

        return ""

    def _validate_mermaid_semantics(self, diagram_code: str, evidence_packet) -> tuple:
        """
        Validate Mermaid diagram semantics (FIX 4 applied - minimal rules only).

        Returns:
            (is_valid, errors_list)
        """
        errors = []
        lines = diagram_code.split('\n')

        # Rule 1: No endpoint nodes with paths/methods
        endpoint_patterns = ['/upload', '/query', '/health', '/api/', 'GET ', 'POST ', 'PUT ', 'DELETE ']
        for line in lines:
            for pattern in endpoint_patterns:
                if pattern in line and '[' in line:
                    errors.append(f"Diagram contains endpoint/route node: {pattern}")
                    break

        # Rule 2: Must include User or Client
        has_user = any(('User' in line or 'Client' in line) and '[' in line for line in lines)
        if not has_user:
            errors.append("Diagram should include User or Client node")

        # Rule 3: Must have Backend if backend exists
        if evidence_packet and evidence_packet.has_backend:
            has_backend = any(('API' in line or 'Backend' in line or 'Server' in line)
                             and '[' in line for line in lines)
            if not has_backend:
                errors.append("Diagram missing Backend/API node (backend detected in repo)")

        # Rule 4: Must have Frontend if frontend exists
        if evidence_packet and evidence_packet.has_frontend:
            has_frontend = any(('Frontend' in line or 'UI' in line or 'Client' in line or 'Web' in line)
                              and '[' in line for line in lines)
            if not has_frontend:
                errors.append(f"Diagram missing Frontend/UI node ({evidence_packet.frontend_framework} detected)")

        # Rule 5: Must have Database if common DB deps found
        if evidence_packet:
            db_deps = ['sqlalchemy', 'psycopg2', 'pymongo', 'mysql', 'redis', 'elasticsearch']
            has_db_dep = any(dep in [d.lower() for d in evidence_packet.python_deps] for dep in db_deps)
            if has_db_dep:
                has_db_node = any(('Database' in line or 'DB' in line or 'Storage' in line or 'Cache' in line)
                                 and '[' in line for line in lines)
                if not has_db_node:
                    errors.append("Diagram missing Database node (database dependency detected)")

        return (len(errors) == 0, errors)

    # QA Validation
    async def qa_validator_node(self, state: DocGenState) -> DocGenState:
        """Run QA Validator agent - validates sections BEFORE assembly with evidence-based guardrails"""
        job_id = state["job_id"]
        readme_sections = state.get("readme_sections", {})
        evidence_packet = state.get("evidence_packet")

        # Start metrics tracking
        metrics = self._get_metrics_collector(job_id)
        metrics.start_agent("QAValidator")

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message="✅ Validating README sections with evidence checks...",
            agent_name="QAValidator"
        )

        llm = get_llm(model_name=settings.QA_VALIDATOR_MODEL, temperature=0.7)
        result = await run_qa_validator_agent(
            llm=llm,
            readme_sections=readme_sections,
            job_id=job_id,
            evidence_packet=evidence_packet
        )

        if result.get("success"):
            qa_output = result.get("output", "")
            # Try to parse QA score
            import json
            try:
                qa_data = json.loads(qa_output)
                state["qa_score"] = qa_data.get("qa_score", 75)
                state["qa_passed"] = qa_data.get("qa_passed", True)
                state["qa_validation_result"] = qa_data
            except:
                state["qa_score"] = 75
                state["qa_passed"] = True
                state["qa_validation_result"] = {"output": qa_output}

            await self.log_manager.log_async(
                job_id=job_id,
                log_type=LogType.SUCCESS,
                message=f"✅ QA Validator completed (Score: {state.get('qa_score', 'N/A')})",
                agent_name="QAValidator"
            )
            # End metrics tracking (success)
            metrics.end_agent(
                "QAValidator",
                success=True,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                tool_calls=result.get("tool_calls", 0),
                llm_calls=result.get("llm_calls", 0)
            )
        else:
            logger.error(f"QAValidator failed: {result.get('error')}")
            # End metrics tracking (failure)
            metrics.end_agent("QAValidator", success=False, error_message=result.get('error'))

        state["current_agent"] = "QAValidator"
        return state

    async def assembly_node(self, state: DocGenState) -> DocGenState:
        """Assemble final README with GenAISamples structure (EXACT logic from docugen)"""
        job_id = state["job_id"]

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message="🔨 Assembling final README..."
        )

        readme_parts = []
        readme_sections = state.get("readme_sections", {})
        mermaid_diagrams = state.get("mermaid_diagrams", {})
        repo_name = state.get('repo_name', 'Project')

        # Helper function to convert kebab-case/snake_case to Title Case
        def to_title_case(text: str) -> str:
            """Convert 'rag-chatbot' or 'doc_summarization' to 'Rag Chatbot' or 'Doc Summarization'"""
            return ' '.join(word.capitalize() for word in text.replace('-', ' ').replace('_', ' ').split())

        # 1. ## Title (H2, not H1!) - Convert to Title Case
        readme_parts.append(f"## {to_title_case(repo_name)}\n\n")

        # 2. Brief intro (extract ONLY first 1-2 sentences from Project Overview as teaser)
        if "Project Overview" in readme_sections:
            overview_content = readme_sections["Project Overview"]
            # Extract content after heading
            lines = overview_content.split('\n')
            content_text = []
            found_heading = False

            for line in lines:
                if line.startswith("## Project Overview"):
                    found_heading = True
                    continue
                if found_heading and line.strip():
                    content_text.append(line.strip())

            # Join all content and split by sentences
            full_text = ' '.join(content_text)
            # Split by period followed by space (basic sentence splitting)
            sentences = [s.strip() + '.' for s in full_text.split('. ') if s.strip()]

            # Take only the first sentence as intro (to avoid duplication)
            if sentences:
                intro = sentences[0]
                readme_parts.append(f"{intro}\n\n")

        # Define explicit section order (chronological)
        SECTION_ORDER = [
            "Project Overview",
            "Features",
            "Architecture",
            "Prerequisites",
            "Quick Start Deployment",
            "User Interface",
            "Configuration",
            "Troubleshooting"
        ]

        # 3. ## Table of Contents (use explicit order)
        readme_parts.append("## Table of Contents\n\n")
        for section in SECTION_ORDER:
            if section in readme_sections:
                anchor = section.lower().replace(" ", "-").replace("/", "")
                readme_parts.append(f"- [{section}](#{anchor})\n")
        readme_parts.append("\n")

        # 4. --- separator
        readme_parts.append("---\n\n")

        # 5. Add all sections in explicit order with --- separators
        architecture_section_found = False

        for section in SECTION_ORDER:
            if section not in readme_sections:
                continue

            content = readme_sections[section]
            # Add section content
            readme_parts.append(content)
            readme_parts.append("\n\n")

            # Insert Architecture diagram RIGHT after Architecture section content
            if section.lower() == "architecture":
                architecture_section_found = True
                if mermaid_diagrams:
                    for diagram_name, diagram_code in mermaid_diagrams.items():
                        readme_parts.append(f"```mermaid\n{diagram_code}\n```\n\n")
                    mermaid_diagrams = {}  # Clear so we don't add again

            # Add --- separator after each section
            readme_parts.append("---\n\n")

        # 6. If diagrams were generated but no Architecture section exists, add minimal Architecture section with diagram
        if mermaid_diagrams and not architecture_section_found:
            readme_parts.append("## Architecture\n\n")
            for diagram_name, diagram_code in mermaid_diagrams.items():
                readme_parts.append(f"```mermaid\n{diagram_code}\n```\n\n")
            readme_parts.append("---\n\n")

        state["final_readme"] = "".join(readme_parts)
        state["workflow_status"] = "completed"

        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.SUCCESS,
            message="✅ Documentation generation complete!"
        )

        # Finalize metrics and log summary
        metrics = self._get_metrics_collector(job_id)
        metrics.finalize_workflow()
        summary = metrics.get_summary()

        # Build per-agent metrics display
        agent_metrics_lines = []
        for agent in summary['agents']:
            if agent['success']:
                # Calculate per-agent TPS (output tokens per second)
                agent_duration_sec = agent['duration_ms'] / 1000 if agent['duration_ms'] > 0 else 0
                agent_tps = agent['output_tokens'] / agent_duration_sec if agent_duration_sec > 0 else 0.0

                agent_metrics_lines.append(
                    f"   ├─ {agent['agent_name']}: total={agent['total_tokens']:,} "
                    f"(out={agent['output_tokens']:,}), {agent['duration_ms']:,.0f}ms, outTPS={agent_tps:.2f}"
                )

        agent_metrics_str = "\n".join(agent_metrics_lines)

        # Log metrics summary to agent logs panel
        await self.log_manager.log_async(
            job_id=job_id,
            log_type=LogType.INFO,
            message=f"\n📊 **Workflow Metrics Summary**\n"
                    f"├─ Total Agents: {summary['workflow']['total_agents']}\n"
                    f"├─ Successful: {summary['workflow']['successful_agents']}\n"
                    f"├─ Failed: {summary['workflow']['failed_agents']}\n"
                    f"├─ Total Duration: {summary['workflow']['total_duration_seconds']}s\n"
                    f"├─ Total Tokens: {summary['workflow']['total_tokens']:,}\n"
                    f"│  ├─ Input: {summary['workflow']['total_input_tokens']:,}\n"
                    f"│  └─ Output: {summary['workflow']['total_output_tokens']:,}\n"
                    f"├─ Total Tool Calls: {summary['workflow']['total_tool_calls']}\n"
                    f"├─ Total LLM Calls: {summary['workflow']['total_llm_calls']}\n"
                    f"├─ Workflow Average TPS: {summary['workflow']['average_tps']} tokens/sec\n"
                    f"│\n"
                    f"├─ **Per-Agent Metrics (Model TPS)**\n"
                    f"{agent_metrics_str}\n"
        )

        logger.info(f"[{job_id}] Metrics Summary: {summary}")

        # Cleanup
        if state.get("repo_path"):
            self.git_service.cleanup_repository(state["repo_path"])

        return state


# Global workflow instance
_workflow: SimplifiedDocuGenWorkflow = None


async def get_workflow() -> SimplifiedDocuGenWorkflow:
    """Get or create workflow instance"""
    global _workflow
    if _workflow is None:
        _workflow = SimplifiedDocuGenWorkflow()
        await _workflow.create_workflow()
    return _workflow

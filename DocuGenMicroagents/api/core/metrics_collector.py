"""
Metrics Collection for Workflow Execution

Tracks real metrics from execution:
- Token usage per agent
- Time to first token (TTFT)
- Tokens per second (TPS)
- Tool calls per agent
- Workflow-level aggregated metrics

Key principle: Measure everything, estimate nothing
"""

import time
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Metrics for a single agent execution"""
    agent_name: str
    job_id: str

    # Execution metrics
    start_time_ms: float = 0
    end_time_ms: float = 0
    duration_ms: float = 0

    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # Tool calling
    llm_calls: int = 0
    tool_calls: int = 0

    # Status
    success: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def calculate_cost(self, cost_per_million_tokens: float = 0.15) -> float:
        """
        Calculate estimated cost in USD

        Args:
            cost_per_million_tokens: Cost per 1M tokens (default: $0.15 for Qwen3-4B estimate)

        Returns:
            Estimated cost in USD
        """
        return (self.total_tokens / 1_000_000) * cost_per_million_tokens

    def calculate_tps(self) -> float:
        """
        Calculate tokens per second (TPS)

        Returns:
            Tokens per second
        """
        if self.duration_ms == 0:
            return 0.0
        duration_seconds = self.duration_ms / 1000
        return self.output_tokens / duration_seconds if duration_seconds > 0 else 0.0


class MetricsCollector:
    """
    Centralized metrics collection for all agents

    Tracks real execution metrics for workflow analysis
    """

    def __init__(self, job_id: str):
        """
        Initialize MetricsCollector

        Args:
            job_id: Unique job identifier
        """
        self.job_id = job_id
        self.agents: Dict[str, AgentMetrics] = {}
        self.workflow_start_time = time.time() * 1000  # Convert to ms
        self.workflow_end_time: Optional[float] = None

        logger.info(f"[{job_id}] MetricsCollector initialized")

    def start_agent(self, agent_name: str) -> AgentMetrics:
        """
        Start tracking an agent

        Args:
            agent_name: Name of agent

        Returns:
            AgentMetrics instance for this agent
        """
        if agent_name in self.agents:
            logger.warning(f"[{self.job_id}] Agent {agent_name} already started, resetting")

        metrics = AgentMetrics(
            agent_name=agent_name,
            job_id=self.job_id,
            start_time_ms=time.time() * 1000
        )

        self.agents[agent_name] = metrics
        logger.debug(f"[{self.job_id}] Started tracking: {agent_name}")

        return metrics

    def end_agent(
        self,
        agent_name: str,
        success: bool = True,
        input_tokens: int = 0,
        output_tokens: int = 0,
        llm_calls: int = 0,
        tool_calls: int = 0,
        error_message: Optional[str] = None
    ):
        """
        End tracking an agent

        Args:
            agent_name: Name of agent
            success: Whether agent succeeded
            input_tokens: Input tokens used
            output_tokens: Output tokens generated
            llm_calls: Number of LLM calls
            tool_calls: Number of tool calls
            error_message: Error message if failed
        """
        if agent_name not in self.agents:
            logger.error(f"[{self.job_id}] Agent {agent_name} not started")
            return

        metrics = self.agents[agent_name]
        metrics.end_time_ms = time.time() * 1000
        metrics.duration_ms = metrics.end_time_ms - metrics.start_time_ms
        metrics.success = success
        metrics.input_tokens = input_tokens
        metrics.output_tokens = output_tokens
        metrics.total_tokens = input_tokens + output_tokens
        metrics.llm_calls = llm_calls
        metrics.tool_calls = tool_calls
        metrics.error_message = error_message

        tps = metrics.calculate_tps()

        logger.info(
            f"[{self.job_id}] {agent_name} completed: "
            f"success={success}, tokens={metrics.total_tokens}, "
            f"duration={metrics.duration_ms:.0f}ms, TPS={tps:.2f}"
        )

    def finalize_workflow(self):
        """Mark workflow as complete and calculate final metrics"""
        self.workflow_end_time = time.time() * 1000
        workflow_duration = self.workflow_end_time - self.workflow_start_time

        logger.info(
            f"[{self.job_id}] Workflow completed in {workflow_duration:.0f}ms "
            f"({len(self.agents)} agents)"
        )

    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics summary

        Returns:
            Dictionary with all metrics
        """
        if not self.workflow_end_time:
            self.finalize_workflow()

        # Calculate totals
        total_tokens = sum(m.total_tokens for m in self.agents.values())
        total_input_tokens = sum(m.input_tokens for m in self.agents.values())
        total_output_tokens = sum(m.output_tokens for m in self.agents.values())
        total_tool_calls = sum(m.tool_calls for m in self.agents.values())
        total_llm_calls = sum(m.llm_calls for m in self.agents.values())
        workflow_duration_ms = self.workflow_end_time - self.workflow_start_time

        # Agent-level metrics
        agent_metrics = [m.to_dict() for m in self.agents.values()]

        # Calculate workflow-level TPS
        workflow_duration_seconds = workflow_duration_ms / 1000
        workflow_tps = total_output_tokens / workflow_duration_seconds if workflow_duration_seconds > 0 else 0.0

        # Count failed agents
        failed_agents = [m for m in self.agents.values() if not m.success]

        return {
            "job_id": self.job_id,
            "workflow": {
                "total_agents": len(self.agents),
                "successful_agents": len([m for m in self.agents.values() if m.success]),
                "failed_agents": len(failed_agents),
                "total_duration_ms": workflow_duration_ms,
                "total_duration_seconds": round(workflow_duration_seconds, 2),
                "total_tokens": total_tokens,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_tool_calls": total_tool_calls,
                "total_llm_calls": total_llm_calls,
                "average_tps": round(workflow_tps, 2)
            },
            "agents": agent_metrics,
            "failed_agent_names": [m.agent_name for m in failed_agents]
        }

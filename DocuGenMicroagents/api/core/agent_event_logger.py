"""
Shared Agent Event Logger - Callback Handler for ReAct Pattern Visibility

Captures tool calls and LLM events from LangChain agents and streams them
to the UI via SSE for real-time "Thinking → Action → Observation" display.

Works with both LangChain and LangGraph agents.
"""

import logging
from typing import Any, Dict, List, Optional
from langchain_core.callbacks.base import AsyncCallbackHandler
from models import get_log_manager, LogType

logger = logging.getLogger(__name__)


class AgentEventLogger(AsyncCallbackHandler):
    """
    Callback handler that captures agent events and streams them to UI.

    Captures:
    - Tool calls (Actions)
    - Tool outputs (Observations)
    - LLM starts (Thinking)

    Usage:
        logger = AgentEventLogger(job_id="job_123", agent_name="CodeExplorer")
        result = await agent.ainvoke(..., config={"callbacks": [logger]})
    """

    def __init__(self, job_id: str, agent_name: str):
        """
        Initialize the event logger

        Args:
            job_id: Job ID for streaming logs
            agent_name: Name of the agent (e.g., "CodeExplorer", "Writer")
        """
        super().__init__()
        self.job_id = job_id
        self.agent_name = agent_name
        self.log_manager = get_log_manager()
        self.cycle_count = 0
        self.tool_call_count = 0
        self.current_tool = None

        # Debouncing flags to prevent duplicate logs
        self._agent_started = False
        self._agent_completed = False

        # Tool-specific thinking messages (context-aware)
        self.thinking_templates = {
            "list_directory": "📂 Examining directory structure...",
            "read_file": "📖 Reading file to extract information...",
            "detect_languages": "🔍 Analyzing programming languages...",
            "extract_dependencies": "📦 Extracting project dependencies...",
            "analyze_code_structure": "🏗️ Analyzing code structure and patterns...",
            "find_entry_points": "🎯 Locating application entry points...",
            "find_api_routes": "🌐 Discovering API routes and endpoints...",
            "find_config_files": "⚙️ Finding configuration files...",
            "validate_mermaid_syntax": "✅ Validating diagram syntax...",
            "validate_readme_structure": "📋 Checking README structure...",
            "default": "💭 Analyzing repository and planning next step..."
        }

    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        """
        Called when a tool starts executing (Action step)

        Args:
            serialized: Tool metadata
            input_str: Tool input arguments
        """
        self.cycle_count += 1
        self.tool_call_count += 1

        # Extract tool name
        tool_name = serialized.get("name", "unknown_tool")
        self.current_tool = tool_name

        # Log thinking step before action
        thinking_msg = self.thinking_templates.get(tool_name, self.thinking_templates["default"])
        await self.log_manager.log_async(
            job_id=self.job_id,
            log_type=LogType.AGENT_THINKING,
            message=f"💭 Thinking (Cycle {self.cycle_count}): {thinking_msg}",
            agent_name=self.agent_name,
            metadata={
                "cycle": self.cycle_count,
                "type": "thinking",
                "next_tool": tool_name
            }
        )

        # Format tool arguments for display
        try:
            # Try to parse input_str as it might be JSON or formatted string
            args_display = input_str[:200] if input_str else "(no args)"
            if len(input_str) > 200:
                args_display += "..."
        except:
            args_display = "(args)"

        # Log action step
        await self.log_manager.log_async(
            job_id=self.job_id,
            log_type=LogType.AGENT_ACTION,
            message=f"🔧 Action (Cycle {self.cycle_count}): {tool_name}({args_display})",
            agent_name=self.agent_name,
            metadata={
                "cycle": self.cycle_count,
                "type": "action",
                "tool": tool_name,
                "input": input_str,
                "call_number": self.tool_call_count
            }
        )

    async def on_tool_end(
        self,
        output: str,
        **kwargs: Any
    ) -> None:
        """
        Called when a tool finishes (Observation step)

        Args:
            output: Tool output/result
        """
        tool_name = self.current_tool or "unknown"

        # Create intelligent summary of output
        output_str = str(output)
        output_lines = output_str.count('\n') + 1

        # Smart truncation
        if len(output_str) > 300:
            output_preview = output_str[:300] + f"... [{len(output_str)} chars total, {output_lines} lines]"
        else:
            output_preview = output_str

        # Log observation step
        await self.log_manager.log_async(
            job_id=self.job_id,
            log_type=LogType.AGENT_OBSERVATION,
            message=f"📊 Observation (Cycle {self.cycle_count}): {tool_name} returned:\n{output_preview}",
            agent_name=self.agent_name,
            metadata={
                "cycle": self.cycle_count,
                "type": "observation",
                "tool": tool_name,
                "output_length": len(output_str),
                "line_count": output_lines
            }
        )

    async def on_tool_error(
        self,
        error: Exception,
        **kwargs: Any
    ) -> None:
        """
        Called when a tool encounters an error

        Args:
            error: The exception that occurred
        """
        tool_name = self.current_tool or "unknown"

        await self.log_manager.log_async(
            job_id=self.job_id,
            log_type=LogType.ERROR,
            message=f"❌ Error (Cycle {self.cycle_count}): {tool_name} failed - {str(error)}",
            agent_name=self.agent_name,
            metadata={
                "cycle": self.cycle_count,
                "type": "error",
                "tool": tool_name,
                "error": str(error)
            }
        )

    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any
    ) -> None:
        """
        Called when LLM starts generating (optional - for detailed logging)

        Args:
            serialized: LLM metadata
            prompts: Input prompts
        """
        # Optional: Log LLM reasoning start
        # Only log if we want very detailed visibility
        pass

    async def on_llm_end(
        self,
        response: Any,
        **kwargs: Any
    ) -> None:
        """
        Called when LLM finishes generating

        Args:
            response: LLM response
        """
        # Optional: Log LLM completion
        pass

    async def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """
        Called when agent chain starts
        """
        # Debounce: Only log the first chain start
        if self._agent_started:
            return

        self._agent_started = True

        # Log agent start
        await self.log_manager.log_async(
            job_id=self.job_id,
            log_type=LogType.AGENT_START,
            message=f"🚀 Starting {self.agent_name} agent...",
            agent_name=self.agent_name,
            metadata={"type": "agent_start"}
        )

    async def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """
        Called when agent chain completes
        """
        # Debounce: Only log the first chain end
        if self._agent_completed:
            return

        self._agent_completed = True

        # Log completion summary
        await self.log_manager.log_async(
            job_id=self.job_id,
            log_type=LogType.INFO,
            message=f"✅ Completed {self.cycle_count} ReAct cycle(s) with {self.tool_call_count} tool call(s)",
            agent_name=self.agent_name,
            metadata={
                "type": "agent_complete",
                "total_cycles": self.cycle_count,
                "total_tool_calls": self.tool_call_count
            }
        )

    async def on_chain_error(
        self,
        error: Exception,
        **kwargs: Any
    ) -> None:
        """
        Called when agent chain encounters an error

        Args:
            error: The exception that occurred
        """
        await self.log_manager.log_async(
            job_id=self.job_id,
            log_type=LogType.ERROR,
            message=f"❌ {self.agent_name} agent failed: {str(error)}",
            agent_name=self.agent_name,
            metadata={
                "type": "agent_error",
                "error": str(error)
            }
        )


def create_agent_logger(job_id: str, agent_name: str) -> AgentEventLogger:
    """
    Factory function to create an AgentEventLogger

    Args:
        job_id: Job ID for log streaming
        agent_name: Name of the agent

    Returns:
        Configured AgentEventLogger instance

    Example:
        logger = create_agent_logger("job_123", "CodeExplorer")
        result = await agent.ainvoke(..., config={"callbacks": [logger]})
    """
    return AgentEventLogger(job_id=job_id, agent_name=agent_name)

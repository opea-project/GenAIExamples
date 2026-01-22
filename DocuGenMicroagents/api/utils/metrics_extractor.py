"""
Utility for extracting metrics from LangGraph agent execution results
"""

from typing import Dict, List, Any


def extract_agent_metrics(messages: List[Any]) -> Dict[str, int]:
    """
    Extract token usage and call counts from LangGraph messages.

    Args:
        messages: List of messages from LangGraph agent execution

    Returns:
        Dict with input_tokens, output_tokens, tool_calls, llm_calls
    """
    input_tokens = 0
    output_tokens = 0
    tool_calls = 0
    llm_calls = 0

    for msg in messages:
        # Count tool calls (messages with tool_calls attribute)
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            tool_calls += len(msg.tool_calls)

        # Count LLM calls and extract token usage from AIMessage responses ONLY
        # Check if this is an AIMessage by looking for response_metadata attribute
        if hasattr(msg, 'response_metadata') and msg.__class__.__name__ == 'AIMessage':
            llm_calls += 1
            metadata = msg.response_metadata

            # Try different token usage formats (different LLM providers use different keys)
            if 'usage_metadata' in metadata:
                # LangChain format
                usage = metadata['usage_metadata']
                input_tokens += usage.get('input_tokens', 0)
                output_tokens += usage.get('output_tokens', 0)
            elif 'token_usage' in metadata:
                # OpenAI format
                usage = metadata['token_usage']
                input_tokens += usage.get('prompt_tokens', 0)
                output_tokens += usage.get('completion_tokens', 0)
            elif 'usage' in metadata:
                # Alternative format
                usage = metadata['usage']
                input_tokens += usage.get('input_tokens', usage.get('prompt_tokens', 0))
                output_tokens += usage.get('output_tokens', usage.get('completion_tokens', 0))

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "tool_calls": tool_calls,
        "llm_calls": llm_calls
    }

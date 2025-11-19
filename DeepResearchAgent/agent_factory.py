import os
from datetime import datetime
from typing import Any
from langchain_openai import ChatOpenAI


def create_deepagents_research_agent() -> Any:
    from deepagents import create_deep_agent
    from research_agents.deepagents.prompts import (
        RESEARCHER_INSTRUCTIONS,
        RESEARCH_WORKFLOW_INSTRUCTIONS,
        SUBAGENT_DELEGATION_INSTRUCTIONS,
    )
    from research_agents.deepagents.tools import tavily_search, think_tool

    # Limits
    max_concurrent_research_units = os.environ.get("MAX_CONCURRENT_RESEARCH_UNITS", 3)
    max_researcher_iterations = os.environ.get("MAX_RESEARCHER_ITERATIONS", 3)

    # Custom instructions (if any)
    instructions_researcher=os.environ.get("RESEARCHER_INSTRUCTIONS", RESEARCHER_INSTRUCTIONS)
    instructions_research_workflow=os.environ.get("RESEARCH_WORKFLOW_INSTRUCTIONS", RESEARCH_WORKFLOW_INSTRUCTIONS)
    instructions_subagent_delegation=os.environ.get("SUBAGENT_DELEGATION_INSTRUCTIONS", SUBAGENT_DELEGATION_INSTRUCTIONS)

    # Combine orchestrator instructions (RESEARCHER_INSTRUCTIONS only for sub-agents)
    INSTRUCTIONS = (
        instructions_research_workflow
        + "\n\n"
        + "=" * 80
        + "\n\n"
        + instructions_subagent_delegation.format(
            max_concurrent_research_units=max_concurrent_research_units,
            max_researcher_iterations=max_researcher_iterations,
        )
    )
    
    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Research agent definition
    research_sub_agent = {
        "name": "research-agent",
        "description": "Delegate research to the sub-agent researcher. Only give this researcher one topic at a time.",
        "system_prompt": instructions_researcher.format(date=current_date),
        "tools": [tavily_search, think_tool],
    }

    # LLM serving endpoint
    model = ChatOpenAI(
        openai_api_base=os.environ.get("OPENAI_BASE_URL", "http://0.0.0.0:8000/v1/"),
        openai_api_key=os.environ.get("OPENAI_API_KEY", "empty-api-key"),
        model_name=os.environ.get("LLM_MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct"),
        temperature=0.0
    )
    
    # Create the agent
    return create_deep_agent(
        model=model,
        tools=[tavily_search, think_tool],
        system_prompt=INSTRUCTIONS,
        subagents=[research_sub_agent],
    )
    
def create_agent(impl="DeepAgents") -> Any:
    if impl == "DeepAgents":
        return create_deepagents_research_agent()
    else:
        raise ValueError(f"Unknown agent implementation: {impl}")

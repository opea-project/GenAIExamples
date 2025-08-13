# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any

import yaml


def load_config(config_path: str):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def create_agent(config: str) -> Any:

    config_dict = load_config(config)

    agent_config = config_dict.get("agent")
    agent_type = agent_config.pop("type")

    try:
        import uuid

        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.types import Command

        # from open_deep_research.graph import builder
        # TODO
        from legacy.graph import builder
    except ImportError as e:
        raise ImportError(
            f"Failed to import required modules for langchain deep researcher: {e}. Make sure langgraph and open_deep_research are installed. Also make sure that the benchmark directory is in your path. Also, you might need to install the with-open-deep-research extra dependencies (see README.md)."
        )

    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)

    REPORT_STRUCTURE = """Use this structure to create a report on the user-provided topic:

                1. Introduction (no research needed)
                - Brief overview of the topic area

                2. Main Body Sections:
                - Each section should focus on a sub-topic of the user-provided topic

                3. Conclusion
                - Aim for 1 structural element (either a list of table) that distills the main body sections
                - Provide a concise summary of the report"""

    # Extract configuration parameters
    search_api = agent_config.get("search_api", "tavily")
    planner_provider = agent_config.get("planner_provider")
    planner_model = agent_config.get("planner_model")
    planner_endpoint = agent_config.get("planner_endpoint")
    writer_provider = agent_config.get("writer_provider")
    writer_model = agent_config.get("writer_model")
    writer_endpoint = agent_config.get("writer_endpoint")
    max_search_depth = agent_config.get("max_search_depth", 3)

    async def langchain_wrapper(goal: str):
        thread = {
            "configurable": {
                "thread_id": str(uuid.uuid4()),
                "search_api": search_api,
                "planner_provider": planner_provider,
                "planner_model": planner_model,
                "writer_provider": writer_provider,
                "writer_model": writer_model,
                "max_search_depth": max_search_depth,
                "report_structure": REPORT_STRUCTURE,
            }
        }

        # NOTE: add research prompt to the goal for robust benchmarking purposes
        goal = goal + " You must perform in-depth research to answer the question."

        results = []

        async for event in graph.astream({"topic": goal}, thread, stream_mode="updates"):
            results.append(event)

        async for event in graph.astream(Command(resume=True), thread, stream_mode="updates"):
            results.append(event)

        final_state = graph.get_state(thread)
        report = final_state.values.get("final_report")

        return report

    return langchain_wrapper

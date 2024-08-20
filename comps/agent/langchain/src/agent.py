# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


def instantiate_agent(args, strategy="react_langchain", with_memory=False):
    if strategy == "react_langchain":
        from .strategy.react import ReActAgentwithLangchain

        return ReActAgentwithLangchain(args, with_memory)
    elif strategy == "react_langgraph":
        from .strategy.react import ReActAgentwithLanggraph

        return ReActAgentwithLanggraph(args, with_memory)
    elif strategy == "plan_execute":
        from .strategy.planexec import PlanExecuteAgentWithLangGraph

        return PlanExecuteAgentWithLangGraph(args, with_memory)

    elif strategy == "rag_agent":
        from .strategy.ragagent import RAGAgent

        return RAGAgent(args, with_memory)
    else:
        raise ValueError(f"Agent strategy: {strategy} not supported!")

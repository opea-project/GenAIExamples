# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


def instantiate_agent(args, strategy="react"):
    if strategy == "react":
        from .strategy.react import ReActAgentwithLangchain

        return ReActAgentwithLangchain(args)
    elif strategy == "plan_execute":
        from .strategy.planexec import PlanExecuteAgentWithLangGraph

        return PlanExecuteAgentWithLangGraph(args)
    elif strategy == "agentic_rag":
        from .strategy.agentic_rag import RAGAgentwithLanggraph

        return RAGAgentwithLanggraph(args)
    else:
        from .strategy.base_agent import BaseAgent, BaseAgentState

        return BaseAgent(args)

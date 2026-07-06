# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Configuration models and helpers for Mini Deep Search."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel, Field


class PromptTemplates(BaseModel):
    """Collection of prompt templates used by the DeepSearch workflow."""

    system: str = Field(..., description="Template for the system prompt.")
    generate_query: str = Field(..., description="Instruction for generating the next retrieval query.")
    make_plan: str = Field(..., description="Instruction for constructing the retrieval plan.")
    plan: str = Field(..., description="Format string for presenting the plan back to the model.")
    plan_step: str = Field(..., description="Template used for each individual plan step.")
    context: str = Field(..., description="Template for wrapping a single context chunk.")
    contexts: str = Field(..., description="Template for presenting all contexts for evaluation.")
    continue_decision: str = Field(..., description="Instruction asking the model whether more retrieval is needed.")
    experiences: str = Field(..., description="Template used when experience search results are available.")


class Config(BaseModel):
    """Runtime configuration for the Mini Deep Search pipeline."""

    system_instruction: str
    plan_instruction: str = ""
    query_instruction: str
    answer_instruction: str
    domain_knowledge: str
    retrieve_top_k: int
    rerank_top_k: int
    mece_retrieval: bool = False
    max_retrievals: int
    max_plan_steps: int = 7
    recur_summarize_instruction: str = ""
    postproc: str = "defaults.py"
    use_summarized_context: bool = False
    prompt_templates: PromptTemplates


DEFAULT_CONFIG_DICT: Dict[str, Any] = {
    "system_instruction": "As an expert AI assistant, your goal is to provide accurate solutions. Analyze the user's question, create a retrieval plan, gather information, and synthesize a step-by-step answer. Follow all instructions.",
    "plan_instruction": "To maximize retrieval recall, create a multi-step query plan. First, deconstruct the user's question into its core components and symptoms. Then, generate hypotheses about the potential root causes. Finally, create a numbered list of 2-5 queries to investigate these hypotheses.\n\n*   **Step 1 (Rephrase and Broaden):** Start with a comprehensive query that rephrases the user's question, including synonyms and alternative phrasings to ensure broad initial coverage.\n*   **Subsequent Steps (Hypothesis Testing):** Each following query should be a targeted, self-contained question designed to confirm or deny a specific hypothesis. These queries must include precise technical terms, component names, and potential error codes to retrieve the most relevant documents.\n\nYour final output must be only the numbered list of queries.",
    "query_instruction": "After each retrieval, evaluate if you have enough information to solve the problem. If not, and if your plan has more steps, formulate the next query. This query must be a concise, targeted sub-question with precise keywords to fill a specific knowledge gap. Do not use prefixes like 'Query:'./no_think",
    "answer_instruction": "Synthesize the retrieved information into a final, actionable answer for the user.\n\n**User's Question:**\n{question}\n\n**Retrieved Information:**\n{plan_with_information}\n\n**Your Task:**\n1.  **Synthesize and Filter:** Review all retrieved context, using only the most relevant information to address the user's problem.\n2.  **Structure and Format:** Organize the solution into a clear, step-by-step guide. Present it as a numbered or bulleted list, highlighting any warnings at the beginning.\n\n**Citation Rules (MUST follow):**\n- Use only provided DOCUMENT_NODE evidence.\n- For each claim based on DOCUMENT_NODE_CONTEXT, append citation after the current paragraph:\n  - Chinese answer: (来自 [DOCUMENT_NODE_SOURCE](DOCUMENT_NODE_FILE_PATH))\n  - Non-Chinese answer: (from [DOCUMENT_NODE_SOURCE](DOCUMENT_NODE_FILE_PATH))\n- At the end of the answer, output:\n\n --- \n\n### Document Source:\n- DOCUMENT_NODE_SOURCE\n\nOnly include unique DOCUMENT_NODE_SOURCE values (deduplicated). Do NOT include links/URLs/paths in this final Document Source block./no_think",
    "domain_knowledge": "",
    "prompt_templates": {
        "system": "{system_instruction}\n\n{query_instruction}\n\n{domain_knowledge}\n\n{experiences}\n",
        "generate_query": "Now generate a query for the next retrieval./no_think",
        "make_plan": "Now generate a plan based on the user's question above. \n\n{plan_instruction}\n\nFormat the plan as a (Python) list containing the ordered steps, each step is a string./no_think",
        "plan": "The following is the plan to step by step retrieve knowledge needed and work out an answer to user's question:\n{plan_steps}\n",
        "plan_step": "Step {num}: {step}.",
        "context": "<context>\n{context}\n</context>\n",
        "contexts": "The following are the retrieved contexts for current query.\n{contexts}\n",
        "continue_decision": "Is more information needed? Answer Yes or No. Then explain why or why not.",
        "experiences": "The following are question-plan examples by human experts. Refer to them to better make your plan. If you find that there is a question that is highly similar or exactly match the input question, then strictly follow the subquestions to make the plan.\n\n{experiences}\n",
    },
    "retrieve_top_k": 60,
    "rerank_top_k": 3,
    "mece_retrieval": True,
    "max_retrievals": 3,
    "max_plan_steps": 3,
}


def get_default_config() -> Config:
    """Return the built-in DeepSearch default configuration."""
    return Config(**deepcopy(DEFAULT_CONFIG_DICT))


def _resolve_path(value: str, base_path: Path) -> str:
    """Resolve value relative to ``base_path`` if it is an existing file."""
    if not value:
        return value
    value_path = Path(value)
    if value_path.is_absolute():
        return str(value_path)
    candidate = base_path / value
    return str(candidate) if candidate.exists() else value


def load_config(config_path: str) -> Config:
    """Load and normalise a configuration file.

    Args:
        config_path: Path to the configuration JSON.

    Returns:
        A fully-populated :class:`Config` instance.
    """
    config_file = Path(config_path).expanduser().resolve()
    with config_file.open("r", encoding="utf-8") as handle:
        config_dict: Dict[str, Any] = json.load(handle)

    base_dir = config_file.parent

    # Resolve relative paths where applicable.
    for key in ("domain_knowledge", "postproc"):
        if key in config_dict and isinstance(config_dict[key], str):
            config_dict[key] = _resolve_path(config_dict[key], base_dir)

    cfg = Config(**config_dict)

    # Expand domain knowledge file lazily if it points to a file.
    domain_path = Path(cfg.domain_knowledge)
    if domain_path.exists() and domain_path.is_file():
        cfg.domain_knowledge = domain_path.read_text(encoding="utf-8")

    return cfg

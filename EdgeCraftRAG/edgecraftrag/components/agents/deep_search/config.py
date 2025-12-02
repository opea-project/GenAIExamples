# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Configuration models and helpers for Mini Deep Search."""

from __future__ import annotations

import json
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

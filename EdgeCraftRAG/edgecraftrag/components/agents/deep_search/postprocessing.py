# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Default post-processing logic for Mini Deep Search."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

import json_repair

from .logging_utils import format_terminal_str, log_status


def _merge_plan_steps(plan: List[str], max_steps: int) -> List[str]:
    """Merge plan steps if the generated plan exceeds ``max_steps``."""
    if len(plan) <= max_steps:
        return plan

    merged_plan: List[str] = []
    steps_per_group = len(plan) // max_steps
    extra_steps = len(plan) % max_steps
    index = 0
    for i in range(max_steps):
        group_size = steps_per_group + 1 if i < extra_steps else steps_per_group
        if index < len(plan):
            merged_plan.append(" ".join(plan[index : index + group_size]))
            index += group_size
    log_status(
        "✨",
        format_terminal_str(
            f"Merged plan from {len(plan)} steps to {len(merged_plan)} steps.",
            color="yellow",
            bold=True,
        ),
    )
    return merged_plan


def _extract_pattern_and_text(line: str) -> Optional[Tuple[str, int, str]]:
    match = re.match(r"^(.*?)(\d+)(.*)", line)
    if match:
        prefix, digit_str, text = match.groups()
        if text.strip():
            return prefix, int(digit_str), text.strip()
    return None


def parse_plan_from_text(text_content: str) -> List[str]:
    """Parse a block of text to extract a numbered plan."""
    lines = text_content.splitlines()
    longest_plan: List[str] = []
    for i, start_line in enumerate(lines):
        processed_line = start_line.strip()
        if processed_line.lower().startswith("step"):
            processed_line = re.sub(r"^step\s*[:\-\s#]*", "", processed_line, flags=re.IGNORECASE)
        pattern_info = _extract_pattern_and_text(processed_line)
        if not pattern_info:
            continue
        prefix, digit, text = pattern_info
        if digit not in (0, 1):
            continue
        current_plan = [text]
        expected_digit = digit + 1
        for next_line in lines[i + 1 :]:
            processed_next_line = next_line.strip()
            if processed_next_line.lower().startswith("step"):
                processed_next_line = re.sub(r"^step\s*[:\-\s#]*", "", processed_next_line, flags=re.IGNORECASE)
            expected_pattern = re.match(f"^{re.escape(prefix)}{expected_digit}(.*)", processed_next_line)
            if not expected_pattern:
                break
            next_text = expected_pattern.group(1).strip()
            if not next_text:
                break
            current_plan.append(next_text)
            expected_digit += 1
        if len(current_plan) > len(longest_plan):
            longest_plan = current_plan
    return [step.lstrip(" .:-") for step in longest_plan]


def postproc_plan(text: str, state, cfg) -> List[str]:  # type: ignore[valid-type]
    try:
        plan = json_repair.loads(text)
        if not plan:
            try:
                plan = parse_plan_from_text(text)
            except Exception as exc:  # pragma: no cover - defensive logging only
                log_status(
                    "⚠️",
                    format_terminal_str(
                        f"Error parsing plan from text: {exc}. Using question as single step plan",
                        color="red",
                        bold=True,
                    ),
                )
                plan = None
        elif any(not isinstance(step, str) for step in plan):
            new_plan = []
            for step in plan:
                if isinstance(step, str):
                    new_plan.append(step)
                elif isinstance(step, dict) and "step" in step:
                    new_plan.append(step["step"])
                elif isinstance(step, list) and all(isinstance(s, str) for s in step):
                    new_plan.extend(step)
                else:
                    log_status("⚠️", f"Invalid step format: {step}. Using as-is.")
                    new_plan.append(str(step))
            plan = new_plan
        log_status(
            "✨",
            format_terminal_str(f"Plan created with {len(plan)} steps.", color="cyan", bold=True),
        )
    except Exception as exc:  # pragma: no cover - defensive logging only
        log_status(
            "⚠️",
            format_terminal_str(
                f"Error evaluating plan: {exc}. Using question as single step plan",
                color="red",
                bold=True,
            ),
        )
        plan = None
    plan = plan or [state.question]
    return _merge_plan_steps(plan, cfg.max_plan_steps)


def postproc_query(text: str, state):  # type: ignore[valid-type]
    log_status("💡", f"{format_terminal_str('Query generated:', color='cyan', bold=True)} '{text}'")
    return text, text


def postproc_answer(text: str, state):  # type: ignore[valid-type]
    return text

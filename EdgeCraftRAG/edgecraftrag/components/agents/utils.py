# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import asyncio
import importlib.util
import json
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy
from pydantic import BaseModel

# from wrapped_atomic_apis import call_logits_next_token

# Configure logging
logger = logging.getLogger("deep_search")
logger.setLevel(logging.INFO)

# Create console handler with a formatter that includes timestamps and emojis
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    # Format: [YYYY-MM-DD HH:MM:SS] Message with emoji
    formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def log_status(emoji: str, message: str, indent: int = 0) -> None:
    """Log a formatted status message with emoji indicator using Python's logging module.

    Args:
        emoji: Emoji character to prepend to the message
        message: The message text to log
        indent: Number of indentation levels (2 spaces each)
    """
    indent_str = "  " * indent
    logger.info(f"{indent_str}{emoji} {message}")


class Config(BaseModel):
    system_instruction: str
    plan_instruction: str = ""
    query_instruction: str
    answer_instruction: str
    domain_knowledge: str
    retrieve_top_k: int
    rerank_top_k: int
    max_retrievals: int
    max_plan_steps: int = 7
    embedding_endpoint: str
    reranker_endpoint: str
    llm_endpoint: str
    query_search_endpoint: str = ""
    generation_config: Dict[str, Any] = {}
    postproc: str = "defaults.py"


def import_module_from_path(file_path: str):
    """Import a module from a full file path.

    Args:
        file_path: Full path to the Python file to import

    Returns:
        The imported module

    Raises:
        ImportError: If the module cannot be imported
    """
    if not os.path.isfile(file_path):
        raise ImportError(f"File not found: {file_path}")

    # Get the module name (filename without extension)
    module_name = os.path.splitext(os.path.basename(file_path))[0]

    # Create the spec
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Failed to create spec for: {file_path}")

    # Create the module
    module = importlib.util.module_from_spec(spec)

    # Add the module to sys.modules
    sys.modules[module_name] = module

    # Execute the module
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise ImportError(f"Error executing module {module_name}: {e}")

    return module


def load_config(config_path: str) -> Config:
    """Load configuration from a JSON file.

    Args:
        config_path: Path to the configuration JSON file

    Returns:
        Config object with loaded configuration
    """
    with open(config_path, "r") as f:
        config_dict = json.load(f)
    cfg = Config(**config_dict)
    if os.path.isfile(cfg.domain_knowledge):
        with open(cfg.domain_knowledge, "r") as f:
            cfg.domain_knowledge = f.read()
    return cfg


class ROLE:
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"


def remove_tagged(text, tag="think"):
    pattern = f"<{tag}>.*?</{tag}>"
    return re.sub(pattern, "", text, flags=re.DOTALL).strip()


def _extract_pattern_and_text(line: str) -> Optional[Tuple[str, int, str, str]]:
    """Checks if a line matches the pattern [prefix][digit][suffix][text].

    Args:
        line: The line to check.

    Returns:
        A tuple of (prefix, digit, suffix, step_text) if a match is found,
        otherwise None.
        - prefix: Characters before the digit (e.g., " "). Can be empty.
        - digit: The integer value of the digit.
        - suffix: The separator characters after the digit (e.g., ". ").
        - step_text: The actual description of the step.
    """
    # Pattern: Start, any prefix (non-greedy), a digit, a suffix of non-digits,
    # and the rest of the line as text.
    # The suffix (\D+) is followed by (.*) which will grab the text.
    # This structure correctly separates the separator from the text.
    match = re.match(r"^(.*?)(\d+)(.*)", line)
    if match:
        prefix, digit_str, text = match.groups()
        # We require actual text for it to be a valid step
        if text.strip():
            return prefix, int(digit_str), text.strip()
    return None


def parse_plan_from_text(text_content: str) -> List[str]:
    """Parses a block of text to extract a list of plan steps by finding a
    consecutive sequence of numbered lines.

    Args:
        text_content: A string containing the plan.

    Returns:
        A list of strings, where each string is a single plan step.
    """
    lines = text_content.splitlines()
    longest_plan = []

    # Iterate through each line, treating it as a potential start of a plan
    for i, start_line in enumerate(lines):

        # 1. Pre-process the line
        processed_line = start_line.strip()
        if processed_line.lower().startswith("step"):
            # Remove "step" and any space/punctuation immediately after
            processed_line = re.sub(r"^step\s*[:\-\s#]*", "", processed_line, flags=re.IGNORECASE)

        # 2. Check if it matches the generic pattern and starts with 0 or 1
        pattern_info = _extract_pattern_and_text(processed_line)
        if pattern_info:
            prefix, digit, text = pattern_info

            # Allow multi-digit numbers but only start a plan on 0 or 1
            if digit in [0, 1]:
                current_plan = [text]
                expected_digit = digit + 1

                # 3. If it's a valid start, check subsequent lines for the same pattern
                for next_line in lines[i + 1 :]:

                    # Pre-process the next line similarly
                    processed_next_line = next_line.strip()
                    if processed_next_line.lower().startswith("step"):
                        processed_next_line = re.sub(r"^step\s*[:\-\s#]*", "", processed_next_line, flags=re.IGNORECASE)

                    # Check if the next line matches the *exact* pattern with the next number
                    # We escape prefix/suffix in case they contain special regex characters
                    expected_pattern = re.match(f"^{re.escape(prefix)}{expected_digit}(.*)", processed_next_line)

                    if expected_pattern:
                        next_text = expected_pattern.group(1).strip()
                        if next_text:  # Ensure the step is not empty
                            current_plan.append(next_text)
                            expected_digit += 1
                        else:
                            break  # Empty step text breaks sequence
                    else:
                        # The consecutive sequence is broken
                        break

                # If the plan we just found is the longest so far, save it
                if len(current_plan) > len(longest_plan):
                    longest_plan = current_plan
    longest_plan = [_.lstrip(" .:-") for _ in longest_plan]
    return longest_plan


def format_terminal_str(text: str, color: str = "", bold: bool = False, italic: bool = False) -> str:
    """Format a string with ANSI escape codes for color, bold, and italic.

    Args:
        text: The text to format.
        color: The color name (e.g., 'red', 'green', 'blue').
        bold: Whether to apply bold formatting.
        italic: Whether to apply italic formatting.

    Returns:
        The formatted string with ANSI codes.

    Notes:
        - If the environment variable NO_COLOR is set (per https://no-color.org/),
          the function returns the original text without styling.
        - Unsupported color names are ignored (text returned with other
          requested styles, if any).
        - Color names are case-insensitive. Both standard and bright variants
          are supported (e.g., 'red', 'bright_red').
    """
    if text is None:
        text = ""

    # Honor NO_COLOR convention
    if os.environ.get("NO_COLOR"):
        return text

    color_lower = color.lower()

    # Standard and bright ANSI color codes
    color_map = {
        "black": 30,
        "red": 31,
        "green": 32,
        "yellow": 33,
        "blue": 34,
        "magenta": 35,
        "cyan": 36,
        "white": 37,
        "bright_black": 90,
        "bright_red": 91,
        "bright_green": 92,
        "bright_yellow": 93,
        "bright_blue": 94,
        "bright_magenta": 95,
        "bright_cyan": 96,
        "bright_white": 97,
    }

    style_seq: List[str] = []

    # Add color if valid
    if color_lower in color_map:
        style_seq.append(str(color_map[color_lower]))

    # Bold and italic attributes
    if bold:
        style_seq.append("1")
    if italic:
        style_seq.append("3")

    # If no styling requested or recognized, return original text
    if not style_seq:
        return text

    prefix = f"\033[{';'.join(style_seq)}m"
    suffix = "\033[0m"
    return f"{prefix}{text}{suffix}"


_LLM_EVAL_DEFAULT_TEMPLATE_MESSAGES = [
    {
        "role": "system",
        "content": """You are an impartial quality rater for troubleshooting answers. Your task is to rate if the answer by user well covers the steps in the reference answer.

Task instructions:
- Parse the reference answer into its essential checkpoints (split on punctuation such as "?", ";", or line breaks) and understand what each step expects the technician to do or verify. The order of the checkpoints has low importance.
- Examine the user's answer and decide if each checkpoint is substantively addressed with accurate, actionable guidance.
- Treat synonymous language or additional helpful context as a match when it fulfills the intent of the checkpoint.
- Mark a checkpoint as uncovered if the user's answer omits it, contradicts it, or gives incorrect or unsafe guidance.
- Ignore extra steps that do not conflict with the reference; they should not reduce the score.
- The mismatch of the step number between user's answer and reference answer does not matter, as long as all the content is well covered.
- Keep all reasoning internal; do not expose the intermediate analysis in the final reply.
- Focus solely on the provided texts. Do not rely on your knowledge.
""",
    },
    {
        "role": "user",
        "content": """User's answer:
{llm_answer}

Reference answer:
{ref_answer}
""",
        "template_message": True,
    },
    {
        "role": "system",
        "content": """Does the user's answer well cover the steps in the reference answer? Yes or No.

Scoring rubric:
- Answer "Yes" only when every checkpoint from the reference is fully covered and nothing in the user's answer conflicts with the reference guidance.
- Answer "No" if any checkpoint is missing, incorrectly addressed, or contradicted by the user's answer.
""",
    },
    {"role": "assistant", "content": '{"label": "'},
]
DEFAULT_TARGET_TOKENS = ["No", "Yes"]
DEFAULT_TRANSFORM_PARAMS = (5, -1, 10)  # a, b, T


def batch_cal_score(x, a=1.0, b=0.0, T=1.0, s=10):
    _, d = x.shape
    levels = numpy.arange(d)[None,] / (d - 1)
    transformed = numpy.exp(x / T)
    probs = transformed / transformed.sum(axis=1, keepdims=True)
    expected_levels = (probs * levels).sum(axis=1)
    scores = a * expected_levels + b
    return s * numpy.tanh(scores)


def llm_evaluate(
    ref_answer,
    llm_answer,
    eval_endpoint,
    template_messages=_LLM_EVAL_DEFAULT_TEMPLATE_MESSAGES,
    target_tokens=DEFAULT_TARGET_TOKENS,
    transform_params=DEFAULT_TRANSFORM_PARAMS,
    return_logits=False,
) -> Union[float, List[float]]:
    messages = [
        (
            message
            if not message.get("template_message")
            else {
                "role": message["role"],
                "content": message["content"].format(ref_answer=ref_answer, llm_answer=llm_answer),
            }
        )
        for message in template_messages
    ]
    # result_json = call_logits_next_token(
    #     endpoint=eval_endpoint,
    #     messages=messages,
    #     target_tokens=target_tokens
    # )
    result_json = ""
    raw_logits = {_["token"]: _["logit"] for _ in result_json["target_token_logits"]}
    raw_logits = [raw_logits[k] for k in target_tokens]
    if return_logits:
        return raw_logits
    else:
        score = batch_cal_score(numpy.array(raw_logits)[None,], *transform_params)[0]
        return score


def remove_think_tags(text: str) -> str:
    """Remove <think>...</think> sections from Qwen3 output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

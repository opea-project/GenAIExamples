# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Logging helpers for Mini Deep Search."""

import logging
import os
from typing import List

_LOGGER_NAME = "deep_search"


def _configure_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


LOGGER = _configure_logger()


def log_status(emoji: str, message: str, indent: int = 0) -> None:
    """Emit a formatted status message with optional indent."""
    indent_str = "  " * indent
    LOGGER.info("%s%s %s", indent_str, emoji, message)


def format_terminal_str(text: str, color: str = "", bold: bool = False, italic: bool = False) -> str:
    """Format ``text`` with ANSI colours, bold or italics."""
    if text is None:
        text = ""

    if os.environ.get("NO_COLOR"):
        return text

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
    if color and color.lower() in color_map:
        style_seq.append(str(color_map[color.lower()]))
    if bold:
        style_seq.append("1")
    if italic:
        style_seq.append("3")

    if not style_seq:
        return text

    prefix = f"\033[{';'.join(style_seq)}m"
    return f"{prefix}{text}\033[0m"

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Internal helper utilities for Mini Deep Search."""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from enum import Enum
from typing import Optional


class Role(str, Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"


def import_module_from_path(file_path: str):
    """Import and return a Python module from the given path."""
    if not os.path.isfile(file_path):
        raise ImportError(f"File not found: {file_path}")

    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Failed to create spec for: {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        if spec.loader is None:
            raise ImportError(f"Module loader missing for: {file_path}")
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - propagates import errors
        raise ImportError(f"Error executing module {module_name}: {exc}") from exc
    return module


def remove_tagged(text: str, tag: str = "think") -> str:
    """Remove sections wrapped in a custom tag from ``text``."""
    pattern = f"<{tag}>.*?</{tag}>"
    return re.sub(pattern, "", text, flags=re.DOTALL).strip()

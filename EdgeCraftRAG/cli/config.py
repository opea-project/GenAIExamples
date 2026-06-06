# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Configuration for EdgeCraft RAG CLI."""

import os
from typing import Optional


class CLIConfig:
    """CLI configuration from environment variables."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        self.host = os.getenv("ECRAG_HOST", "http://localhost")
        self.port = int(os.getenv("ECRAG_PORT", "16010"))
        self.mega_port = int(os.getenv("ECRAG_MEGA_PORT", "16011"))

    def get_server_url(self) -> str:
        """Get the server URL."""
        return f"{self.host}:{self.port}"

    def get_mega_url(self) -> str:
        """Get the mega service URL."""
        return f"{self.host}:{self.mega_port}"


def get_config() -> CLIConfig:
    """Get CLI configuration."""
    return CLIConfig()

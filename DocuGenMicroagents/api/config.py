"""
Configuration management for DocuGen AI
Supports GenAI Gateway and Keycloak authentication
"""

import os
from enum import Enum
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class AuthMode(str, Enum):
    """Authentication mode enumeration"""
    GENAI_GATEWAY = "genai_gateway"
    KEYCLOAK = "keycloak"


class Settings(BaseSettings):
    """Application settings with multi-auth support"""

    # Application Info
    APP_TITLE: str = "DocuGen Micro-Agents"
    APP_DESCRIPTION: str = "AI-powered documentation generation with specialized micro-agent system"
    APP_VERSION: str = "1.0.0"

    # Server Configuration
    API_PORT: int = 5001
    HOST: str = "0.0.0.0"

    # CORS Settings
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]

    # Authentication Mode
    AUTH_MODE: AuthMode = AuthMode.GENAI_GATEWAY

    # GenAI Gateway Configuration
    GENAI_GATEWAY_URL: Optional[str] = None
    GENAI_GATEWAY_API_KEY: Optional[str] = None

    # Keycloak Configuration (Enterprise)
    BASE_URL: Optional[str] = None
    KEYCLOAK_REALM: str = "master"  # Keycloak realm (typically "master")
    KEYCLOAK_CLIENT_ID: str = "api"  # Client ID for service account
    KEYCLOAK_CLIENT_SECRET: Optional[str] = None  # Client secret for authentication

    # Micro-Agent Model Configuration (Using SLM - Qwen3-4B)
    CODE_EXPLORER_MODEL: str = "Qwen/Qwen3-4B-Instruct-2507"
    API_REFERENCE_MODEL: str = "Qwen/Qwen3-4B-Instruct-2507"
    CALL_GRAPH_MODEL: str = "Qwen/Qwen3-4B-Instruct-2507"
    ERROR_ANALYSIS_MODEL: str = "Qwen/Qwen3-4B-Instruct-2507"
    ENV_CONFIG_MODEL: str = "Qwen/Qwen3-4B-Instruct-2507"
    DEPENDENCY_ANALYZER_MODEL: str = "Qwen/Qwen3-4B-Instruct-2507"
    PLANNER_MODEL: str = "Qwen/Qwen3-4B-Instruct-2507"
    MERMAID_MODEL: str = "Qwen/Qwen3-4B-Instruct-2507"
    QA_VALIDATOR_MODEL: str = "Qwen/Qwen3-4B-Instruct-2507"
    WRITER_MODEL: str = "Qwen/Qwen3-4B-Instruct-2507"


    # Repository Settings
    TEMP_REPO_DIR: str = "./tmp/repos"
    MAX_REPO_SIZE: int = 10737418240  # 10GB in bytes
    MAX_FILE_SIZE: int = 1000000  # 1MB
    MAX_FILES_TO_SCAN: int = 500
    MAX_LINES_PER_FILE: int = 500  # Line budget per file (pattern_window extracts ~150-300 lines)

    # GitHub Integration (for MCP PR creation)
    GITHUB_TOKEN: Optional[str] = None

    # Agent Settings
    AGENT_TEMPERATURE: float = 0.7
    AGENT_MAX_TOKENS: int = 1000
    AGENT_TIMEOUT: int = 300  # 5 minutes

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

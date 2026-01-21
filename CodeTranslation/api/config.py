"""
Configuration settings for Code Translation API
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Custom API Configuration for Keycloak
BASE_URL = os.getenv("BASE_URL", "https://api.example.com")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "api")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")

# Model Configuration for CodeLlama-34b-instruct
INFERENCE_MODEL_ENDPOINT = os.getenv("INFERENCE_MODEL_ENDPOINT", "CodeLlama-34b-Instruct")
INFERENCE_MODEL_NAME = os.getenv("INFERENCE_MODEL_NAME", "codellama/CodeLlama-34b-Instruct-hf")

# Validate required configuration
if not KEYCLOAK_CLIENT_SECRET:
    raise ValueError("KEYCLOAK_CLIENT_SECRET must be set in environment variables")

# Application Settings
APP_TITLE = "Code Translation API"
APP_DESCRIPTION = "AI-powered code translation service using CodeLlama-34b-instruct"
APP_VERSION = "1.0.0"

# File Upload Settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf"}

# Code Translation Settings
SUPPORTED_LANGUAGES = ["java", "c", "cpp", "python", "rust", "go"]
MAX_CODE_LENGTH = 10000  # characters
LLM_TEMPERATURE = 0.2  # Lower temperature for more deterministic code generation
LLM_MAX_TOKENS = 4096

# CORS Settings
CORS_ALLOW_ORIGINS = ["*"]  # Update with specific origins in production
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

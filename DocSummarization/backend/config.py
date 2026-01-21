"""
Configuration settings for Doc-Sum Application
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enterprise/Keycloak Configuration (Required for LLM)
BASE_URL = os.getenv("BASE_URL")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "api")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")

# Model Configuration (Enterprise Inference)
INFERENCE_MODEL_ENDPOINT = os.getenv("INFERENCE_MODEL_ENDPOINT", "Llama-3.1-8B-Instruct")
INFERENCE_MODEL_NAME = os.getenv("INFERENCE_MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")

# LLM Configuration
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

# Validate configuration (checked at runtime, not on import)
# KEYCLOAK_CLIENT_SECRET is required for text summarization

# Application Settings
APP_TITLE = "Document Summarization Service"
APP_DESCRIPTION = "AI-powered document summarization with enterprise inference integration"
APP_VERSION = "2.0.0"

# Service Configuration
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# File Upload Settings
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(500 * 1024 * 1024)))  # 500MB
MAX_PDF_SIZE = int(os.getenv("MAX_PDF_SIZE", str(50 * 1024 * 1024)))  # 50MB

# File Processing Limits
MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "100"))  # Maximum pages to process from PDF
WARN_PDF_PAGES = 50  # Warn user if PDF has more than this many pages

# CORS Settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

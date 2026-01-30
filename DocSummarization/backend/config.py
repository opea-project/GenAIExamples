"""
Configuration settings for Doc-Sum Application
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Inference API Configuration
INFERENCE_API_ENDPOINT = os.getenv("INFERENCE_API_ENDPOINT", "https://api.example.com")
INFERENCE_API_TOKEN = os.getenv("INFERENCE_API_TOKEN")

# Model Configuration
INFERENCE_MODEL_NAME = os.getenv("INFERENCE_MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")

# LLM Configuration
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

# Docker Configuration
LOCAL_URL_ENDPOINT = os.getenv("LOCAL_URL_ENDPOINT", "not-needed")

# Validate required configuration
if not INFERENCE_API_ENDPOINT or not INFERENCE_API_TOKEN:
    raise ValueError("INFERENCE_API_ENDPOINT and INFERENCE_API_TOKEN must be set in .env file")

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
CORS_ALLOW_ORIGINS = ["*"]  # Update with specific origins in production
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

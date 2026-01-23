"""
Configuration settings for Multi-Agent Q&A API
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Custom API Configuration
BASE_URL = os.getenv("BASE_URL", "https://api.example.com")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "api")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")

# Model Configuration
EMBEDDING_MODEL_ENDPOINT = os.getenv("EMBEDDING_MODEL_ENDPOINT", "bge-base-en-v1.5")
INFERENCE_MODEL_ENDPOINT = os.getenv("INFERENCE_MODEL_ENDPOINT", "Llama-3.1-8B-Instruct")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "bge-base-en-v1.5")
INFERENCE_MODEL_NAME = os.getenv("INFERENCE_MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")

# Validate required configuration
if not OPENAI_API_KEY and not KEYCLOAK_CLIENT_SECRET:
    raise ValueError("Either OPENAI_API_KEY or KEYCLOAK_CLIENT_SECRET must be set in environment variables")

# Application Settings
APP_TITLE = "Multi-Agent Q&A"
APP_DESCRIPTION = "A multi-agent Q&A system using CrewAI"
APP_VERSION = "1.0.0"

# CORS Settings
CORS_ALLOW_ORIGINS = ["*"]  # Update with specific origins in production
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]


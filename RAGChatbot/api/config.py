"""
Configuration settings for RAG Chatbot API
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
APP_TITLE = "RAG QnA Chatbot"
APP_DESCRIPTION = "A RAG-based chatbot API using LangChain and FAISS"
APP_VERSION = "2.0.0"

# File Upload Settings
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf"}

# Vector Store Settings
VECTOR_STORE_PATH = "./dmv_index"

# Text Splitting Settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
SEPARATORS = ["\n\n", "\n", " ", ""]

# Retrieval Settings
TOP_K_DOCUMENTS = 4
LLM_MODEL = "gpt-3.5-turbo"
LLM_TEMPERATURE = 0
EMBEDDING_MODEL = "text-embedding-ada-002"

# CORS Settings
CORS_ALLOW_ORIGINS = ["*"]  # Update with specific origins in production
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]


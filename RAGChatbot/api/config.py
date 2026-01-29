"""
Configuration settings for RAG Chatbot API
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Inference API Configuration
# Supports multiple inference deployment patterns:
#   - GenAI Gateway: Provide your GenAI Gateway URL and API key
#   - APISIX Gateway: Provide your APISIX Gateway URL and authentication token
INFERENCE_API_ENDPOINT = os.getenv("INFERENCE_API_ENDPOINT", "https://api.example.com")
INFERENCE_API_TOKEN = os.getenv("INFERENCE_API_TOKEN")

# Model Configuration
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "bge-base-en-v1.5")
INFERENCE_MODEL_NAME = os.getenv("INFERENCE_MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")

# Validate required configuration
if not INFERENCE_API_ENDPOINT or not INFERENCE_API_TOKEN:
    raise ValueError("INFERENCE_API_ENDPOINT and INFERENCE_API_TOKEN must be set in environment variables")

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


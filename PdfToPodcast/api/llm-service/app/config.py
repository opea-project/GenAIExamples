from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """LLM Service Configuration"""

    # Service info
    SERVICE_NAME: str = "LLM Script Generation Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8002

    # API Keys
    OPENAI_API_KEY: Optional[str] = None

    # Custom API Configuration
    BASE_URL: Optional[str] = None
    KEYCLOAK_REALM: str = "master"
    KEYCLOAK_CLIENT_ID: str = "api"
    KEYCLOAK_CLIENT_SECRET: Optional[str] = None

    # Model Configuration
    INFERENCE_MODEL_ENDPOINT: str = "DeepSeek-R1-Distill-Qwen-32B"
    INFERENCE_MODEL_NAME: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"

    # Model settings
    DEFAULT_MODEL: str = "gpt-4o-mini"  # Updated to current model
    DEFAULT_TONE: str = "conversational"
    DEFAULT_MAX_LENGTH: int = 2000

    # Generation parameters
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 4000
    MAX_RETRIES: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

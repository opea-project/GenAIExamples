from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """LLM Service Configuration"""

    # Service info
    SERVICE_NAME: str = "LLM Script Generation Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8002

    # Inference API Configuration
    INFERENCE_API_ENDPOINT: Optional[str] = None
    INFERENCE_API_TOKEN: Optional[str] = None
    INFERENCE_MODEL_NAME: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"

    # Model settings
    DEFAULT_TONE: str = "conversational"
    DEFAULT_MAX_LENGTH: int = 2000

    # Generation parameters
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 4000
    MAX_RETRIES: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()

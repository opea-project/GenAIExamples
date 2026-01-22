from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """PDF Service Configuration"""

    # Service info
    SERVICE_NAME: str = "PDF Processing Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8001

    # File processing
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "uploads"

    # OCR settings
    TESSERACT_CMD: Optional[str] = None  # Path to tesseract (None = auto-detect)
    OCR_LANGUAGE: str = "eng"
    OCR_DPI: int = 300

    # Text processing
    ENABLE_TEXT_CLEANING: bool = True
    ENABLE_OCR_FALLBACK: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

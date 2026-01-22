from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """TTS Service Configuration"""

    # Service info
    SERVICE_NAME: str = "TTS Audio Generation Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8003

    # API Keys
    OPENAI_API_KEY: Optional[str] = None

    # TTS settings
    TTS_MODEL: str = "tts-1-hd"  # or tts-1 for faster/cheaper
    DEFAULT_HOST_VOICE: str = "alloy"
    DEFAULT_GUEST_VOICE: str = "nova"

    # Audio settings
    OUTPUT_DIR: str = "static/audio"
    AUDIO_FORMAT: str = "mp3"
    AUDIO_BITRATE: str = "192k"
    SILENCE_DURATION_MS: int = 500

    # Processing
    MAX_CONCURRENT_REQUESTS: int = 5
    MAX_SCRIPT_LENGTH: int = 100  # Max dialogue turns

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

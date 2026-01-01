# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Application configuration Centralized settings management following 12-factor app principles."""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Application
    APP_NAME: str = "OPEA IMS - Cogniware"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # API Configuration
    API_V1_PREFIX: str = "/api"
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://frontend:3000").split(",")

    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION_USE_openssl_rand_hex_32")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/opea_ims")
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")
    REDIS_MAX_CONNECTIONS: int = 50

    # OPEA Services
    OPEA_EMBEDDING_URL: str = os.getenv("OPEA_EMBEDDING_URL", "http://embedding-service:6000")
    OPEA_LLM_URL: str = os.getenv("OPEA_LLM_URL", "http://llm-service:9000")
    OPEA_RETRIEVAL_URL: str = os.getenv("OPEA_RETRIEVAL_URL", "http://retrieval-service:7000")
    OPEA_GATEWAY_URL: str = os.getenv("OPEA_GATEWAY_URL", "http://opea-gateway:8888")

    # Models
    EMBEDDING_MODEL_ID: str = "BAAI/bge-base-en-v1.5"
    LLM_MODEL_ID: str = "Intel/neural-chat-7b-v3-3"
    EMBEDDING_DIMENSION: int = 768
    MAX_TOTAL_TOKENS: int = 2048

    # Data
    CSV_DATA_DIR: str = os.getenv("CSV_DATA_DIR", "/app/data")
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB

    # Logging
    LOG_FILE: str = "/app/logs/app.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"

    # Performance
    WORKER_TIMEOUT: int = 120
    KEEPALIVE_TIMEOUT: int = 5
    MAX_WORKERS: int = 4

    # Feature Flags
    ENABLE_MONITORING: bool = True
    ENABLE_WEBSOCKETS: bool = True
    ENABLE_KNOWLEDGE_UPLOAD: bool = True

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT.lower() == "development"

    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as list."""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()

"""Application configuration management"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Linkarr"
    APP_VERSION: str = "0.1.0-build.7"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Celery
    CELERY_BROKER_URL: str = ""  # Defaults to REDIS_URL if not set
    CELERY_RESULT_BACKEND: str = ""  # Defaults to REDIS_URL if not set

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # TMDb
    TMDB_API_KEY: str
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"

    # Real-Debrid
    RD_API_BASE_URL: str = "https://api.real-debrid.com/rest/1.0"
    RD_LINK_EXPIRY_HOURS: int = 4

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        """Initialize settings with fallback values"""
        super().__init__(**kwargs)

        # Set Celery URLs to Redis if not explicitly configured
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL

        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL


settings = Settings()

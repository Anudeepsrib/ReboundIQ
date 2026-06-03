from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Literal
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "ReboundIQ API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENV: Literal["development", "staging", "production"] = "development"

    # DB / Infra
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"

    # AI Gateway (local-first)
    AI_PROVIDER: Literal["ollama", "vllm", "openai", "anthropic", "gemini", "groq", "litellm", "azure", "bedrock"] = "ollama"
    AI_CHAT_MODEL: str = "llama3.2:1b"
    AI_EMBEDDING_MODEL: str = "nomic-embed-text"
    AI_BASE_URL: str = "http://localhost:11434"
    AI_FALLBACK_PROVIDER: Optional[str] = None
    AI_FALLBACK_MODEL: Optional[str] = None
    ENABLE_EXTERNAL_AI: bool = False

    # External keys (loaded only when enabled + consented; never log)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    # Add others as needed (Gemini, Azure, etc via LiteLLM or direct)

    # Storage
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    STORAGE_LOCAL_ROOT: str = "./storage"
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    S3_REGION: str = "us-east-1"

    # Auth / Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str  # 32-byte for Fernet (sensitive fields: visa etc)

    # Hindsight (opt-in)
    HINDSIGHT_ENABLED: bool = False
    HINDSIGHT_BASE_URL: Optional[str] = None
    HINDSIGHT_API_KEY: Optional[str] = None

    # CORS / Rate
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Features
    FEATURE_DEEP_AGENT: bool = True
    FEATURE_HINDSIGHT_MEMORY: bool = False
    FEATURE_VISA_MODE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()

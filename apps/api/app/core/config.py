from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import List, Optional, Literal


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
    AI_PROVIDER: Literal[
        "ollama",
        "vllm",
        "openai",
        "anthropic",
        "gemini",
        "groq",
        "litellm",
        "azure",
        "bedrock",
    ] = "ollama"
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

    # LangChain / LangGraph / LangSmith observability
    LANGSMITH_TRACING: bool = False
    LANGSMITH_PROJECT: str = "reboundiq-local"
    LANGSMITH_ENDPOINT: Optional[str] = None
    LANGGRAPH_CHECKPOINT_BACKEND: Literal["memory", "postgres"] = "memory"
    LANGGRAPH_CHECKPOINT_DATABASE_URL: Optional[str] = None
    LANGGRAPH_CHECKPOINT_SETUP: bool = False

    @model_validator(mode="after")
    def validate_local_mode(self) -> "Settings":
        """Settings validation for local mode (PR-5): ensure sane defaults for ollama/vllm primary."""
        local_providers = ("ollama", "vllm")
        if self.AI_PROVIDER in local_providers:
            if not self.AI_BASE_URL:
                raise ValueError(
                    "AI_BASE_URL must be set for local AI_PROVIDER (ollama/vllm)"
                )
            if not self.AI_CHAT_MODEL:
                raise ValueError("AI_CHAT_MODEL required for local mode")
            if not self.AI_EMBEDDING_MODEL:
                raise ValueError("AI_EMBEDDING_MODEL required for local mode")
            # External must be explicitly opted into; never default-on for local
            # (enforcement also in gateway; this is config-time signal)
        else:
            if not self.ENABLE_EXTERNAL_AI:
                # allow but note: external provider with external disabled will fail at runtime
                pass
        return self

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()

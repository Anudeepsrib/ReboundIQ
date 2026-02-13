"""
Stillpoint Backend - Configuration Management

Loads configuration from config.json and environment variables.
API keys should be stored in environment variables for security.
"""

import os
import json
from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class OpenAIConfig(BaseModel):
    api_key: str = Field(default="sk-your-openai-api-key-here")
    model: str = Field(default="gpt-4-turbo-preview")
    max_tokens: int = Field(default=4096)


class MockConfig(BaseModel):
    enabled: bool = Field(default=True)
    latency_ms: int = Field(default=500)


class LLMConfig(BaseModel):
    provider: Literal["openai", "mock"] = Field(default="mock")
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    mock: MockConfig = Field(default_factory=MockConfig)


class BraveSearchConfig(BaseModel):
    api_key: str = Field(default="your-brave-api-key-here")
    endpoint: str = Field(default="https://api.search.brave.com/res/v1/web/search")
    max_results: int = Field(default=10)


class SearchConfig(BaseModel):
    provider: Literal["brave", "mock"] = Field(default="mock")
    brave: BraveSearchConfig = Field(default_factory=BraveSearchConfig)
    mock: MockConfig = Field(default_factory=MockConfig)


class RateLimitConfig(BaseModel):
    responses_per_hour: int = Field(default=5)
    responses_per_thread: int = Field(default=3)
    responses_per_user_per_day: int = Field(default=10)


class SourceQualityConfig(BaseModel):
    min_tier: int = Field(default=2)
    require_multiple_sources: bool = Field(default=True)


class SafetyConfig(BaseModel):
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    source_quality: SourceQualityConfig = Field(default_factory=SourceQualityConfig)


class ServerConfig(BaseModel):
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8080)


class Settings(BaseModel):
    """Main configuration settings"""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Settings":
        """Load settings from config.json and environment variables"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.json"
        
        # Load from config file if exists
        config_data = {}
        if config_path.exists():
            with open(config_path, "r") as f:
                config_data = json.load(f)
        
        # Create settings from config file
        settings = cls(**config_data)
        
        # Override with environment variables if set
        if os.getenv("OPENAI_API_KEY"):
            settings.llm.openai.api_key = os.getenv("OPENAI_API_KEY")
        
        if os.getenv("BRAVE_API_KEY"):
            settings.search.brave.api_key = os.getenv("BRAVE_API_KEY")
        
        if os.getenv("LLM_PROVIDER"):
            settings.llm.provider = os.getenv("LLM_PROVIDER")
        
        if os.getenv("SEARCH_PROVIDER"):
            settings.search.provider = os.getenv("SEARCH_PROVIDER")
        
        return settings


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings


def reload_settings(config_path: Optional[Path] = None) -> Settings:
    """Reload settings from config file"""
    global _settings
    _settings = Settings.load(config_path)
    return _settings

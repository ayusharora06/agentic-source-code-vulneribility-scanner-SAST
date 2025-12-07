"""
Application settings and configuration
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Basic app settings
    app_name: str = "Agentic Ethical Hacker"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000
    
    # Database settings
    database_url: str = "vulnerability_analysis.db"
    
    # API Keys (optional, for AI models)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Agent settings
    default_model: str = "gpt-4"
    default_temperature: float = 0.1
    max_tokens: Optional[int] = None
    
    # WebSocket settings
    websocket_ping_interval: int = 30
    websocket_ping_timeout: int = 300
    
    # Analysis settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_project_files: int = 100
    analysis_timeout: int = 600  # 10 minutes
    
    # Tool settings
    enable_infer: bool = True
    enable_clang: bool = True
    enable_pattern_analysis: bool = True
    
    # Security settings
    allowed_origins: list = ["*"]
    api_rate_limit: int = 100  # requests per minute
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = "vulnerability_analysis.log"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
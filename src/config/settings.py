"""
Application settings and configuration management
"""
import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(default="development", description="Environment name")
    
    # API Configuration
    api_title: str = Field(default="Multi-Agent System API", description="API title")
    api_version: str = Field(default="v1", description="API version")
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./data/agents.db",
        description="Database connection URL"
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")
    
    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    log_file: str = Field(default="./logs/app.log", description="Log file path")
    log_max_size: str = Field(default="10MB", description="Max log file size")
    log_backup_count: int = Field(default=5, description="Number of log backup files")
    
    # File Storage
    upload_dir: str = Field(default="./data/uploads", description="Upload directory")
    max_file_size: int = Field(default=10485760, description="Max file size in bytes")
    allowed_extensions: List[str] = Field(
        default=[
            "jpg", "jpeg", "png", "gif", "bmp", "webp",
            "pdf", "txt", "docx", "mp3", "wav", "mp4", "avi"
        ],
        description="Allowed file extensions"
    )
    
    # Agent Configuration
    agent_timeout: int = Field(default=300, description="Agent timeout in seconds")
    max_concurrent_agents: int = Field(
        default=10,
        description="Maximum number of concurrent agents"
    )
    agent_memory_size: int = Field(
        default=1000,
        description="Agent memory size (number of messages)"
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(
        default=100,
        description="Number of requests per window"
    )
    rate_limit_window: int = Field(
        default=60,
        description="Rate limit window in seconds"
    )
    
    # Model Provider Configuration
    # OpenAI
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI base URL"
    )
    openai_default_model: str = Field(
        default="gpt-4-turbo-preview",
        description="Default OpenAI model"
    )
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key"
    )
    anthropic_default_model: str = Field(
        default="claude-3-sonnet-20240229",
        description="Default Anthropic model"
    )
    
    # Ollama
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama base URL"
    )
    ollama_default_model: str = Field(
        default="llama3.2:1b",
        description="Default Ollama model"
    )
    ollama_timeout: int = Field(default=60, description="Ollama timeout in seconds")
    
    # Hugging Face
    hf_token: Optional[str] = Field(default=None, description="Hugging Face token")
    hf_cache_dir: str = Field(
        default="./data/models",
        description="Hugging Face models cache directory"
    )
    
    # Vision Models
    vision_model_provider: str = Field(
        default="openai",
        description="Vision model provider (openai, anthropic, ollama)"
    )
    vision_model_name: str = Field(
        default="gpt-4-vision-preview",
        description="Vision model name"
    )
    
    # Audio Models
    audio_model_provider: str = Field(
        default="openai",
        description="Audio model provider"
    )
    whisper_model: str = Field(default="whisper-1", description="Whisper model name")
    
    # Embedding Models
    embedding_provider: str = Field(
        default="openai",
        description="Embedding model provider"
    )
    embedding_model: str = Field(
        default="text-embedding-ada-002",
        description="Embedding model name"
    )
    embedding_dimension: int = Field(
        default=1536,
        description="Embedding dimension"
    )
    
    # Observability & Monitoring
    langsmith_api_key: Optional[str] = Field(
        default=None,
        description="LangSmith API key for observability"
    )
    langsmith_project: str = Field(
        default="multi-agent-system",
        description="LangSmith project name"
    )
    
    # Prometheus monitoring
    prometheus_enabled: bool = Field(
        default=False,
        description="Enable Prometheus metrics"
    )
    prometheus_port: int = Field(default=9090, description="Prometheus port")
    health_check_interval: int = Field(
        default=30,
        description="Health check interval in seconds"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached)"""
    return Settings()


# Export settings instance
settings = get_settings()
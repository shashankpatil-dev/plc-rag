"""
Application Settings and Configuration
Loads environment variables and provides typed configuration access
"""
from pydantic_settings import BaseSettings
from typing import List, Literal
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_env: Literal["development", "production"] = "development"

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-small"

    # Google Gemini Configuration
    google_api_key: str = ""
    google_model: str = "gemini-pro"

    # OpenRouter Configuration (Unified API for all models)
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_embedding_model: str = "openai/text-embedding-3-small"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Vector Database - Pinecone
    pinecone_api_key: str = ""
    pinecone_environment: str = "us-west1-gcp"
    pinecone_index_name: str = "plc-logic-patterns"

    # Vector Database - ChromaDB
    chromadb_host: str = "localhost"
    chromadb_port: int = 8001
    chromadb_collection: str = "plc_embeddings"

    # Provider Selection
    llm_provider: Literal["openai", "gemini", "openrouter"] = "openrouter"
    embedding_provider: Literal["openai", "gemini", "openrouter"] = "gemini"  # Separate from LLM provider
    embedding_dimensions: int = 1536  # Dimension for embeddings (768 for Gemini, 1536 for OpenAI)
    vector_db_provider: Literal["pinecone", "chromadb"] = "chromadb"

    # CORS Settings
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # File Upload
    max_upload_size: int = 10485760  # 10MB

    # LLM Generation Settings
    max_generation_tokens: int = 8192  # Maximum tokens for L5X generation (reduced for Gemini compatibility)
    generation_temperature: float = 0.1  # Low temperature for consistent output
    generation_timeout: int = 300  # Timeout in seconds for LLM generation (5 minutes)
    generation_max_retries: int = 2  # Maximum retry attempts on timeout

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

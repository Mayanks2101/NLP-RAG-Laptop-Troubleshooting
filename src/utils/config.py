# src/utils/config.py
"""
Configuration management module.

This module loads all settings from environment variables (.env file)
using Pydantic Settings. Benefits:
- Type validation (catches config errors early)
- Auto-completion in IDEs
- Centralized access to all settings
- Easy to override for testing

Usage:
    from src.utils.config import settings
    print(settings.GROQ_API_KEY)
    print(settings.TOP_K)  # Already converted to int!
"""

from pathlib import Path

# FIX: Import get_logger at the TOP of the file.
# logger.py does NOT import from config.py, so there is no circular import.
# Previously it was imported at the bottom AFTER settings = Settings() ran,
# which caused a NameError if TOP_K > 20 (validator called get_logger before it existed).
from src.utils.logger import get_logger

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

logger = get_logger(__name__)


class Settings(BaseSettings):
    """
    Application configuration settings.
    
    All fields are loaded from environment variables.
    Field names in Python (UPPER_SNAKE_CASE) match .env variable names.
    
    Pydantic automatically:
    - Converts strings to correct types (int, float, bool)
    - Validates values (e.g., ensures TOP_K > 0)
    - Provides default values if env var is missing
    """
    
    # === API Keys ===
    GROQ_API_KEY: str = Field(..., description="API key for Groq LLM service")
    
    # === Model Configuration ===
    EMBEDDING_MODEL: str = Field(
        default="BAAI/bge-base-en-v1.5",
        description="HuggingFace model name for text embeddings"
    )
    LLM_MODEL: str = Field(
        default="llama-3.1-8b-instant",
        description="Model name on Groq platform"
    )
    
    # === Qdrant Vector Database ===
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)
    COLLECTION_NAME: str = Field(
        default="laptop_troubleshooting",
        description="Name of Qdrant collection for our data"
    )
    
    # === Data Paths ===
    DATA_DIR: Path = Field(
        default=Path("./data/raw"),
        description="Directory containing preprocessed .txt files"
    )
    PROCESSED_DIR: Path = Field(
        default=Path("./data/processed"),
        description="Directory for cached/processed data"
    )
    
    # === Retrieval Settings ===
    TOP_K: int = Field(
        default=5,
        ge=1,  # Greater than or equal to 1
        description="Number of chunks to retrieve for answering questions"
    )
    SCORE_THRESHOLD: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0-1) to include a result"
    )
    
    # === LLM Generation Settings ===
    LLM_TEMPERATURE: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Controls randomness in LLM responses (lower = more deterministic)"
    )
    LLM_MAX_TOKENS: int = Field(
        default=1024,
        ge=1,
        le=4096,
        description="Maximum tokens in generated answer"
    )
    
    # === Logging ===
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: Path = Field(default=Path("./logs/app.log"))
    
    # === Pydantic Settings Config ===
    model_config = SettingsConfigDict(
        env_file=".env",  # Load from .env file
        env_file_encoding="utf-8",
        case_sensitive=False,  # Treat ENV_VAR and env_var as same
        extra="ignore"  # Ignore extra env vars not defined here
    )
    
    # === Validators (Custom validation logic) ===
    
    @field_validator("DATA_DIR", "PROCESSED_DIR", "LOG_FILE", mode="before")
    @classmethod
    def convert_to_path(cls, v) -> Path:
        """Ensure path fields are Path objects"""
        return Path(v) if isinstance(v, str) else v
    
    @field_validator("TOP_K")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        """Ensure TOP_K is reasonable for retrieval"""
        if v > 20:
            # get_logger is now imported at module level so this works safely
            logger.warning(f"TOP_K={v} is high, may slow down responses")
        return v
    
    def ensure_dirs_exist(self) -> None:
        """
        Create directories for data and logs if they don't exist.
        Call this after loading settings to ensure paths are ready.
        """
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


# Create a singleton instance - import this everywhere you need config
settings = Settings()

# Ensure required directories exist
settings.ensure_dirs_exist()

logger.info(f"Configuration loaded | Collection: {settings.COLLECTION_NAME}")
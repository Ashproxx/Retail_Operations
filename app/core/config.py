"""Validated, explicitly loaded environment configuration."""
from typing import Literal
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RETAILOPS_", env_file=".env", extra="ignore")
    app_name: str = "RetailOps AI"
    environment: Literal["development", "test", "production"] = "development"
    database_url: SecretStr = SecretStr("sqlite+pysqlite:///:memory:")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    routing_confidence_threshold: float = Field(default=0.65, ge=0, le=1)
    max_rag_iterations: int = Field(default=3, ge=1, le=10)
    llm_provider: Literal["ollama", "deterministic", "azure_openai", "openai"] = "ollama"

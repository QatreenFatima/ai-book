"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    neon_db_url: str
    admin_api_key: str = "changeme"
    chat_model: str = "qwen/qwen3-max"
    embedding_model: str = "openai/text-embedding-3-small"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

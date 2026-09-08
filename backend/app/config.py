from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "StorePulse"
    database_url: str = (
        "postgresql+asyncpg://storepulse:storepulse_dev_only@postgres:5432/storepulse"
    )
    frontend_origin: str = "http://localhost:5173"
    offline_threshold_seconds: int = Field(default=30, ge=1, le=3600)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

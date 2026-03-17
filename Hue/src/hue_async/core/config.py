# src/hue_async/core/config.py
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Strongly-typed settings loaded from environment variables and/or .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Hue Bridge info
    HUE_BRIDGE_IP: str
    HUE_USERNAME: str | None = None
    HUE_CLIENTKEY: str | None = None

    # Local web server
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Local web auth for phase 1
    WEB_USERNAME: str = "admin"
    WEB_PASSWORD: str = "change-me"
    WEB_SESSION_SECRET: str = "change-this-secret"


@lru_cache
def get_settings() -> Settings:
    return Settings()
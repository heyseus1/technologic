# src/hue_async/core/config.py
from __future__ import annotations

"""
Configuration for the Hue project.

Why this exists:
- We want ONE place to read environment variables (.env) and provide defaults.
- This keeps scripts/CLI and the future API server from duplicating config logic.
- pydantic-settings reads from:
  1) real environment variables (exported in your shell), then
  2) the .env file (because we specify env_file=".env")
- Type validation is automatic (PORT is an int, etc.)
- We cache Settings so calling get_settings() repeatedly is cheap and consistent.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Strongly-typed settings loaded from environment variables and/or .env.

    Env var naming:
    - We keep names uppercase to match common .env conventions.
    - These names must match what's in your .env file.

    NOTE:
    - HUE_USERNAME is the value returned by the registration step.
    - For Hue API v2 requests, this value is used as the
      'hue-application-key' HTTP header.
    """

    # Tell pydantic-settings where to load values from when they aren't already
    # in the process environment.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unrecognized keys in .env instead of erroring
    )

    # Hue Bridge info (local network)
    # Required for anything that talks to your bridge.
    HUE_BRIDGE_IP: str

    # Hue registration output.
    # This is the "username" returned by POST https://<bridge>/api.
    # Hue v2 calls use this as: header "hue-application-key: <HUE_USERNAME>"
    HUE_USERNAME: str | None = None

    # Optional. Only needed for certain advanced Hue features (streaming, etc.).
    # Not required for basic room/lights control.
    HUE_CLIENTKEY: str | None = None

    # Local server defaults (later, when we host FastAPI locally)
    HOST: str = "127.0.0.1"
    PORT: int = 8000


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings object.

    Why cache:
    - In an API server or CLI, code might call get_settings() many times.
    - We want to parse .env once and reuse the same Settings instance.
    """
    return Settings()

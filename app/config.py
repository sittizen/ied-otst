from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OTRPG_", case_sensitive=False)

    database_url: str = "sqlite:///./app.db"

    session_cookie_name: str = "session_id"
    session_ttl_seconds: int = 60 * 60 * 24 * 14  # 14 days
    cookie_secure: bool = False


settings = Settings()

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """The only place that reads the environment (rules.md 3.7)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Content Intelligence Platform"
    api_version: str = "0.1.0"
    supabase_url: str | None = None
    database_url: str | None = None
    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def supabase_issuer(self) -> str | None:
        return f"{self.supabase_url.rstrip('/')}/auth/v1" if self.supabase_url else None


@lru_cache
def get_settings() -> Settings:
    return Settings()

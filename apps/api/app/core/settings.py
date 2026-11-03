from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """The only place that reads the environment (rules.md 3.7)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Content Intelligence Platform"
    api_version: str = "0.1.0"


def get_settings() -> Settings:
    return Settings()

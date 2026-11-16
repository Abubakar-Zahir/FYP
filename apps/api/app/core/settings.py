from enum import StrEnum
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_LLM_MONTHLY_BUDGET_USD = 30.0


class LlmProviderName(StrEnum):
    # OpenRouter and Gemini both expose this API. A provider with its own API gets its own value.
    OPENAI_COMPATIBLE = "openai_compatible"


class Settings(BaseSettings):
    """The only place that reads the environment (rules.md 3.7)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Content Intelligence Platform"
    api_version: str = "0.1.0"
    supabase_url: str | None = None
    database_url: str | None = None
    redis_url: str | None = None
    cors_origins: list[str] = ["http://localhost:3000"]

    token_encryption_key: SecretStr | None = None
    instagram_app_id: str | None = None
    instagram_app_secret: SecretStr | None = None
    # The web app's /connect/instagram page, registered on the Meta app.
    instagram_redirect_uri: str | None = None

    r2_account_id: str | None = None
    r2_access_key: str | None = None
    r2_secret_key: SecretStr | None = None
    r2_bucket: str | None = None

    # Whisper size for the DNA worker. P0-11 compares tiny and small on Urdu.
    whisper_model: str = "small"
    dna_cut_threshold: float = Field(default=27.0, gt=0)

    llm_provider: LlmProviderName | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    llm_monthly_budget_usd: float = Field(default=DEFAULT_LLM_MONTHLY_BUDGET_USD, gt=0)
    # From the provider's price page. Required, because the budget guard needs them.
    llm_input_usd_per_million_tokens: float | None = Field(default=None, ge=0)
    llm_output_usd_per_million_tokens: float | None = Field(default=None, ge=0)

    @property
    def supabase_issuer(self) -> str | None:
        return f"{self.supabase_url.rstrip('/')}/auth/v1" if self.supabase_url else None


@lru_cache
def get_settings() -> Settings:
    return Settings()

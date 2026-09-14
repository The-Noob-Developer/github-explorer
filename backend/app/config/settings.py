"""Centralized application settings.

Every environment variable the backend depends on is declared here, once, and
read via `get_settings()` everywhere else in the codebase. No module outside
this file should touch `os.environ` directly -- that keeps configuration
auditable (we can grep this one file to know every knob the service has) and
makes it trivial to override settings in tests via `Settings(**overrides)`
instead of monkeypatching environment variables.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated application configuration loaded from the environment."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Groq -----------------------------------------------------------
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-120b", alias="GROQ_MODEL")
    groq_timeout_seconds: float = Field(default=10.0, alias="GROQ_TIMEOUT_SECONDS")

    # --- GitHub -----------------------------------------------------------
    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    github_graphql_url: str = Field(
        default="https://api.github.com/graphql", alias="GITHUB_GRAPHQL_URL"
    )
    github_rest_url: str = Field(
        default="https://api.github.com", alias="GITHUB_REST_URL"
    )
    github_timeout_seconds: float = Field(default=10.0, alias="GITHUB_TIMEOUT_SECONDS")

    # --- Caching ------------------------------------------------------------
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    cache_enabled: bool = Field(default=True, alias="CACHE_ENABLED")
    cache_ttl_seconds: int = Field(default=60, alias="CACHE_TTL_SECONDS")

    # --- Topic resolution -----------------------------------------------
    confidence_threshold: float = Field(default=0.80, alias="CONFIDENCE_THRESHOLD")

    # --- Search limits --------------------------------------------------
    max_results: int = Field(default=100, alias="MAX_RESULTS")

    # --- Rate limiting -----------------------------------------------------
    rate_limit_per_minute: int = Field(default=30, alias="RATE_LIMIT_PER_MINUTE")

    # --- CORS ---------------------------------------------------------------
    allowed_origin: str = Field(default="http://localhost:3000", alias="ALLOWED_ORIGIN")

    
    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origin.split(",") if origin.strip()]



@lru_cache
def get_settings() -> Settings:
    """Return a cached `Settings` instance.

    `lru_cache` gives us a process-wide singleton without any module-level
    mutable state -- the settings object itself is immutable once built, so
    it is safe to share across concurrent async requests.
    """

    return Settings()
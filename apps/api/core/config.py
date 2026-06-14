from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None

    aiml_api_key: str | None = None
    aiml_default_model: str | None = None
    featherless_api_key: str | None = None
    featherless_default_model: str | None = None
    llm_provider: str = "mock"

    embedding_provider: str = "mock"
    embedding_model: str | None = None
    embedding_dimensions: int = Field(default=1536, ge=1)

    band_mode: str = "mock"
    band_api_key: str | None = None
    band_agent_id: str | None = None
    band_default_room_id: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


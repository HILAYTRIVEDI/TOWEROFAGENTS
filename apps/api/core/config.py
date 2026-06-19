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
    # Private Supabase Storage bucket for uploaded workflow artifacts. Created
    # by migration 003. Server-side (service-role) uploads only.
    documents_bucket: str = "workflow-documents"
    # Reject uploads larger than this at the trust boundary. Fixed cap; not yet
    # driven by per-org plan or quota.
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, ge=1)

    aiml_api_key: str | None = None
    aiml_default_model: str | None = None
    featherless_api_key: str | None = None
    featherless_default_model: str | None = None
    featherless_base_url: str = "https://api.featherless.ai/v1"
    # Tool-capable model for the live Band coordinator. Defaults to
    # featherless_default_model when unset. The Band LangGraph adapter sends
    # replies via platform tools, so this model MUST support OpenAI tool calling.
    featherless_tool_model: str | None = None
    llm_provider: str = "mock"

    embedding_provider: str = "mock"
    embedding_model: str | None = None
    embedding_dimensions: int = Field(default=1536, ge=1)

    band_mode: str = "mock"
    band_api_key: str | None = None
    band_agent_id: str | None = None
    band_default_room_id: str | None = None
    # Optional Band platform endpoint overrides. The coordinator falls back to
    # Band's public defaults when these are unset.
    thenvoi_ws_url: str | None = None
    thenvoi_rest_url: str | None = None
    # Optional handle for the reviewer @mentioned by the final agent at end of
    # a workflow run (e.g. "alice" for @alice). When unset the coordinator or
    # first-roster agent is used as a fallback. Never hardcode a value here.
    band_reviewer_handle: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


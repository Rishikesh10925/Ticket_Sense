from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> parents[2] is the repo root, where the shared .env lives.
_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ROOT_ENV, env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"
    database_url: str = "postgresql+asyncpg://ticketsense:ticketsense@localhost:5432/ticketsense"

    jwt_secret_key: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10

    # Selects the LLMProvider the draft-generation pipeline uses (see
    # ai/generation/provider_factory.py). Only "stub" exists today — no paid LLM API
    # key is available in this project's environment, see llm_interface.py.
    llm_provider: str = "stub"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> parents[2] is the repo root, where the shared .env lives.
_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ROOT_ENV, env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"
    database_url: str = "postgresql+asyncpg://ticketsense:ticketsense@localhost:5432/ticketsense"

    @field_validator("database_url")
    @classmethod
    def _use_asyncpg_driver(cls, v: str) -> str:
        # Managed Postgres hosts (Render, Heroku-style) hand out a plain
        # postgresql:// or postgres:// connection string — create_async_engine needs
        # an async-capable driver in the scheme, so this normalizes either into the
        # asyncpg one rather than requiring every deploy target's env var to be
        # hand-edited to match what this app happens to use internally.
        if v.startswith("postgres://"):
            return "postgresql+asyncpg://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            return "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    jwt_secret_key: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    @model_validator(mode="after")
    def _real_secret_outside_development(self) -> "Settings":
        # Week 11 security check: with the default or the .env.example placeholder, anyone
        # can sign a valid admin token. Allowed for local development and tests only.
        weak = len(self.jwt_secret_key) < 32 or self.jwt_secret_key.startswith(("dev-only-", "changeme"))
        if weak and self.app_env not in ("development", "test"):
            raise ValueError("JWT_SECRET_KEY must be a real secret (32+ characters) when APP_ENV is "
                             f"{self.app_env!r}; generate one with: python -c \"import secrets; "
                             "print(secrets.token_hex(32))\"")
        return self

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10

    # The drafting LLM client (ai/generation/llm.py, ADR 002): "ollama" for the local
    # GPU model, "stub" for an offline extractive drafter (CI, tests, no GPU).
    llm_client: str = "ollama"
    # Claim checker: "nli" (cross-encoder, the real one) or "lexical" (CI and tests).
    grounding_scorer: str = "nli"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

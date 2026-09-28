from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/fastapi_service/app/core/config.py -> repo root is 5 levels up.
REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    jwt_signing_key: str = Field(min_length=16)
    jwt_issuer: str
    jwt_audience: str
    service_api_key: str = Field(min_length=16)
    django_internal_url: str = "http://django:8000"
    cors_allowed_origins: str = ""

    # Auto-loads the repo-root .env for local development if present; real
    # process environment variables (e.g. injected by Docker) always win.
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.cors_allowed_origins.split(",") if item.strip()]
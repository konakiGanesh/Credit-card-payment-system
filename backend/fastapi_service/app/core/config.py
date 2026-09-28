from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jwt_signing_key: str = Field(min_length=16)
    jwt_issuer: str
    jwt_audience: str
    service_api_key: str = Field(min_length=16)
    django_internal_url: str = "http://django:8000"
    cors_allowed_origins: str = ""

    model_config = SettingsConfigDict(extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.cors_allowed_origins.split(",") if item.strip()]
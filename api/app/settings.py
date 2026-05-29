import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    app_env: str = "local"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    # "json" emits structured JSON logs (CloudWatch/Log Insights friendly),
    # "text" is human-readable
    log_format: str = "text"
    cors_origins: list[str] = ["http://localhost:5173"]
    table_name: str = "coffee-cards"
    aws_region: str = "ap-southeast-2"
    dynamodb_endpoint_url: str | None = None


class LocalSettings(AppSettings):
    model_config = SettingsConfigDict(case_sensitive=False)


class ProdSettings(AppSettings):
    log_format: str = "json"
    model_config = SettingsConfigDict(case_sensitive=False)


@lru_cache
def get_settings() -> AppSettings:
    app_env = os.environ.get("APP_ENV")
    if app_env == "local":
        return LocalSettings()
    if app_env == "prod":
        return ProdSettings(app_env="prod")
    raise RuntimeError(f"Unknown APP_ENV={app_env!r}. Expected 'local' or 'prod'.")

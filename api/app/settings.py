import logging
import os
from functools import lru_cache
from typing import Any

from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

logger = logging.getLogger(__name__)


class AppSettings(BaseSettings):
    app_env: str = "local"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    log_format: str = "%(asctime)s %(levelname)s %(name)s %(message)s"
    cors_origins: list[str] = ["http://localhost:5173"]
    table_name: str = "coffee-cards"
    aws_region: str = "ap-southeast-2"
    dynamodb_endpoint_url: str | None = None


class LocalSettings(AppSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


class _SsmSource(PydanticBaseSettingsSource):
    """Bulk-load parameters from SSM Parameter Store under a path prefix."""

    def __init__(self, settings_cls: type[AppSettings], ssm_path: str) -> None:
        super().__init__(settings_cls)
        self._path = ssm_path
        self._data: dict[str, Any] = {}

    def _fetch(self) -> dict[str, Any]:
        if self._data:
            return self._data
        try:
            import boto3

            client = boto3.client("ssm")
            paginator = client.get_paginator("get_parameters_by_path")
            for page in paginator.paginate(Path=self._path, WithDecryption=True):
                for p in page["Parameters"]:
                    key = p["Name"].rsplit("/", 1)[-1]  # /prefix/key → key
                    self._data[key] = p["Value"]
        # TODO better exception method
        except Exception:
            logger.exception("SSM load failed for path %s", self._path)
        return self._data

    def get_field_value(self, field: FieldInfo, field_name: str) -> Any:
        return self._fetch().get(field_name)

    def __call__(self) -> dict[str, Any]:
        return self._fetch()


class ProdSettings(AppSettings):
    model_config = SettingsConfigDict(env_file=None, case_sensitive=False)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Priority: init kwargs → Lambda env vars → SSM Parameter Store
        return (
            init_settings,
            env_settings,
            _SsmSource(settings_cls, "/coffee-card/prod/"),
        )


@lru_cache
def get_settings() -> AppSettings:
    app_env = os.environ.get("APP_ENV")
    if app_env == "local":
        return LocalSettings()
    if app_env == "prod":
        return ProdSettings(app_env="prod")
    raise RuntimeError(f"Unknown APP_ENV={app_env!r}. Expected 'local' or 'prod'.")

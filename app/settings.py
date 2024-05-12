import logging
import os
import typing

import aiocache
import pydantic
import pydantic_settings


class DatabaseSettings(pydantic_settings.BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: pydantic.SecretStr
    POSTGRES_NAME: str

    @property
    def ASYNC_DATABASE_URI(self) -> pydantic.PostgresDsn:  # noqa: N802
        return pydantic.PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_NAME,
        )

    @property
    def DATABASE_URI(self) -> pydantic.PostgresDsn:  # noqa: N802
        return pydantic.PostgresDsn.build(
            scheme="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_NAME,
        )


class AppSettings(pydantic_settings.BaseSettings):
    ENVIRONMENT: typing.Literal["stage", "prod"]
    DEBUG: bool

    SECRET_KEY: pydantic.SecretStr
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int

    CACHE_TYPE: type[aiocache.BaseCache] = aiocache.Cache.MEMORY

    @property
    def is_dev(self) -> bool:
        return self.ENVIRONMENT != "prod"

    @property
    def LOGGING_LEVEL(self) -> int:  # noqa: N802
        if self.DEBUG:
            return logging.DEBUG
        return logging.INFO


class Settings(
    AppSettings,
    DatabaseSettings,
):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()

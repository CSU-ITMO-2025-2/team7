from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    user: str = "admin"
    password: str = "admin"
    host: str = "localhost"
    port: int = 5432
    database: str = "core_db"

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", extra="ignore")

    @property
    def async_url(self) -> str:
        return (
            f"postgresql+psycopg_async://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class S3Settings(BaseSettings):
    bucket: str = "core"
    endpoint_url: str = "http://localhost:9000"
    access_key_id: str = "admin"
    secret_access_key: str = "admin123"

    model_config = SettingsConfigDict(env_prefix="S3_", extra="ignore")


class Settings(BaseSettings):
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    s3: S3Settings = Field(default_factory=S3Settings)

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = Settings()


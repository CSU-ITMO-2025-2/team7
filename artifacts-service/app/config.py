from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    user: str
    password: str
    host: str
    port: int
    database: str

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", extra="ignore")

    @property
    def async_url(self) -> str:
        return (
            f"postgresql+psycopg_async://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class S3Settings(BaseSettings):
    bucket: str
    endpoint_url: str
    access_key_id: str
    secret_access_key: str

    model_config = SettingsConfigDict(env_prefix="S3_", extra="ignore")


class AuthSettings(BaseSettings):
    secret: str = "secret"
    algorithm: str = "HS256"
    expires_minutes: int = 60

    model_config = SettingsConfigDict(env_prefix="JWT_", extra="ignore")


class Settings(BaseSettings):
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    s3: S3Settings = Field(default_factory=S3Settings)
    auth: AuthSettings = Field(default_factory=AuthSettings)

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = Settings()

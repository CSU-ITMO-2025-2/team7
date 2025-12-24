from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    url: str

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", extra="ignore", env_file=".env")


class S3Settings(BaseSettings):
    bucket: str
    endpoint_url: str | None = None
    region: str = "us-east-1"
    access_key_id: str | None = None
    secret_access_key: str | None = None

    model_config = SettingsConfigDict(env_prefix="S3_", extra="ignore", env_file=".env")


class KafkaSettings(BaseSettings):
    bootstrap_servers: str
    topic_name: str

    model_config = SettingsConfigDict(env_prefix="KAFKA_", extra="ignore", env_file=".env")


class AuthSettings(BaseSettings):
    secret: str
    algorithm: str = "HS256"
    expires_minutes: int = 60

    model_config = SettingsConfigDict(env_prefix="JWT_", extra="ignore", env_file=".env")


class Settings(BaseSettings):
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    s3: S3Settings = Field(default_factory=S3Settings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = Settings()

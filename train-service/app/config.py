from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Settings(BaseSettings):
    bucket: str
    endpoint_url: str
    access_key_id: str
    secret_access_key: str

    model_config = SettingsConfigDict(env_prefix="S3_", extra="ignore", env_file=".env")


class KafkaSettings(BaseSettings):
    bootstrap_servers: str
    topic_name: str

    model_config = SettingsConfigDict(env_prefix="KAFKA_", extra="ignore", env_file=".env")


class Settings(BaseSettings):
    s3: S3Settings = Field(default_factory=S3Settings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = Settings()

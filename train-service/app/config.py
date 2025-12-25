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
    group_id: str = "train-service"
    auto_offset_reset: str = "earliest"

    model_config = SettingsConfigDict(env_prefix="KAFKA_", extra="ignore", env_file=".env")


class CoreServiceSettings(BaseSettings):
    base_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

    model_config = SettingsConfigDict(env_prefix="CORE_", extra="ignore", env_file=".env")


class TrainSettings(BaseSettings):
    mode: str = "local"  # allowed: kafka | local
    message_json: str | None = None
    message_path: str | None = "message.json"

    model_config = SettingsConfigDict(env_prefix="TRAIN_", extra="ignore", env_file=".env")


class Settings(BaseSettings):
    s3: S3Settings = Field(default_factory=S3Settings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    core_service: CoreServiceSettings = Field(default_factory=CoreServiceSettings)
    train: TrainSettings = Field(default_factory=TrainSettings)

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = Settings()

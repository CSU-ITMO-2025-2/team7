from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Settings(BaseSettings):
    bucket: str
    endpoint_url: str
    access_key_id: str
    secret_access_key: str

    model_config = SettingsConfigDict(env_prefix="S3_", extra="ignore", env_file=".env")


class KafkaSettings(BaseSettings):
    bootstrap_servers: str = "kafka:9092"
    topic_name: str = "runs"
    group_id: str = "train-service"
    auto_offset_reset: str = "earliest"
    security_protocol: str = "PLAINTEXT"
    username: str | None = None
    password: str | None = None

    model_config = SettingsConfigDict(env_prefix="KAFKA_", extra="ignore", env_file=".env")


class CoreServiceSettings(BaseSettings):
    base_url: str = "http://localhost:8000"
    jwt_secret: str = "secret"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

    model_config = SettingsConfigDict(env_prefix="CORE_", extra="ignore", env_file=".env")


class ApiSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8005

    model_config = SettingsConfigDict(env_prefix="TRAIN_", extra="ignore", env_file=".env")


class Settings(BaseSettings):
    s3: S3Settings = Field(default_factory=S3Settings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    core_service: CoreServiceSettings = Field(default_factory=CoreServiceSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = Settings()

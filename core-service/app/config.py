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


class AuthSettings(BaseSettings):
    secret: str = "secret"
    algorithm: str = "HS256"
    expires_minutes: int = 60

    model_config = SettingsConfigDict(env_prefix="JWT_", extra="ignore")


class KafkaSettings(BaseSettings):
    bootstrap_servers: str = "kafka:9092"
    topic: str = "runs"

    model_config = SettingsConfigDict(env_prefix="KAFKA_", extra="ignore")


class ArtifactsServiceSettings(BaseSettings):
    url: str = "http://localhost:8001"

    model_config = SettingsConfigDict(env_prefix="ARTIFACTS_SERVICE_", extra="ignore")


class Settings(BaseSettings):
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    artifacts_service: ArtifactsServiceSettings = Field(default_factory=ArtifactsServiceSettings)

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = Settings()

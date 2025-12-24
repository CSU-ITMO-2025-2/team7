from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    s3_bucket: str
    kafka_bootstrap_servers: str
    kafka_topic_runs: str
    jwt_secret: str

    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"
    s3_endpoint_url: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = Settings()  # raises ValidationError on missing required env vars

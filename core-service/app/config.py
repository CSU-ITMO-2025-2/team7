import os
from dataclasses import dataclass


@dataclass
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg_async://postgres:postgres@localhost:5432/postgres",
    )
    aws_access_key_id: str | None = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    s3_endpoint_url: str | None = os.getenv("S3_ENDPOINT_URL")
    s3_bucket: str = os.getenv("S3_BUCKET", "datasets")
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic_runs: str = os.getenv("KAFKA_TOPIC_RUNS", "runs")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expires_minutes: int = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))


settings = Settings()

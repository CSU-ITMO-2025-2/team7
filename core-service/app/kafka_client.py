import json
from typing import Any

from kafka import KafkaProducer
from kafka.errors import KafkaError

from .config import settings


def get_kafka_producer() -> KafkaProducer:
    """Create and return a Kafka producer instance."""
    config: dict[str, Any] = {
        "bootstrap_servers": settings.kafka.bootstrap_servers,
        "value_serializer": lambda v: json.dumps(v).encode("utf-8"),
        "security_protocol": settings.kafka.security_protocol.upper(),
    }
    if settings.kafka.username and settings.kafka.password:
        config["sasl_plain_username"] = settings.kafka.username
        config["sasl_plain_password"] = settings.kafka.password
    return KafkaProducer(**config)


def send_run_message(producer: KafkaProducer, message: dict[str, Any]) -> None:
    """Send a message to the Kafka runs topic.

    Args:
        producer: KafkaProducer instance
        message: Dictionary containing run information

    Raises:
        KafkaError: If message fails to send
    """
    future = producer.send(settings.kafka.topic, value=message)
    try:
        # Block until message is sent (with timeout)
        future.get(timeout=10)
    except KafkaError as exc:
        raise exc

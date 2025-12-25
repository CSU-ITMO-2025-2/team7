import json
from typing import Any

from kafka import KafkaProducer
from kafka.errors import KafkaError

from .config import settings


def get_kafka_producer() -> KafkaProducer:
    """Create and return a Kafka producer instance."""
    return KafkaProducer(
        bootstrap_servers=settings.kafka.bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


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


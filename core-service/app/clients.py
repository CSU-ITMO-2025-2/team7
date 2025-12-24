import json
from typing import Any

import aiobotocore.session
from confluent_kafka import Producer

from .config import settings

_aio_session = aiobotocore.session.get_session()
_producer: Producer | None = None


async def get_s3_client():
    async with _aio_session.create_client(
        "s3",
        region_name=settings.aws_region,
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    ) as client:
        yield client


def get_kafka_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})
    return _producer


def close_kafka_producer():
    global _producer
    if _producer is not None:
        _producer.flush(5)
        _producer = None


def send_run_message(producer: Producer, payload: dict[str, Any]) -> None:
    producer.produce(settings.kafka_topic_runs, value=json.dumps(payload).encode("utf-8"))
    producer.flush(5)

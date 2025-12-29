import aiobotocore.session
import httpx

from .config import settings

_aio_session = aiobotocore.session.get_session()


async def get_s3_client():
    async with _aio_session.create_client(
        "s3",
        endpoint_url=settings.s3.endpoint_url,
        aws_access_key_id=settings.s3.access_key_id,
        aws_secret_access_key=settings.s3.secret_access_key,
    ) as client:
        yield client


async def get_core_client():
    async with httpx.AsyncClient(base_url=settings.core_service.base_url) as client:
        yield client

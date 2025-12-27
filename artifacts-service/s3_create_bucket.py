import asyncio

import aiobotocore.session
from app.config import settings
from botocore.exceptions import ClientError


async def create_bucket() -> None:
    session = aiobotocore.session.get_session()
    bucket_name = settings.s3.bucket

    async with session.create_client(
        "s3",
        endpoint_url=settings.s3.endpoint_url,
        aws_access_key_id=settings.s3.access_key_id,
        aws_secret_access_key=settings.s3.secret_access_key,
    ) as s3:
        try:
            await s3.head_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' already exists")
            return
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code not in {"404", "NoSuchBucket", "NotFound"}:
                raise

        create_args: dict[str, object] = {"Bucket": bucket_name}

        await s3.create_bucket(**create_args)
        await s3.get_waiter("bucket_exists").wait(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' created")


if __name__ == "__main__":
    asyncio.run(create_bucket())

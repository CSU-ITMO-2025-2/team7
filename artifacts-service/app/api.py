import csv
import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .clients import get_s3_client
from .config import settings
from .database import get_session
from .models import Dataset
from .schemas import DatasetOut

router = APIRouter()


async def _validate_csv(file: UploadFile) -> tuple[bytes, list[str]]:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file is empty")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="file must be utf-8 csv"
        )

    stream = io.StringIO(text)
    try:
        reader = csv.reader(stream)
        headers = next(reader, None)
        if not headers or all(not header.strip() for header in headers):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="csv must contain header row"
            )
        normalized_headers = [header.strip() for header in headers]
        if not any(header.lower() == "target" for header in normalized_headers):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="csv must contain target column"
            )
        if len(headers) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="csv must have at most 50 columns"
            )
        row_count = 0
        for row in reader:
            row_count += 1
            if len(row) != len(headers):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="csv rows must match header column count",
                )
            if len(row) > 50:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="csv must have at most 50 columns",
                )
            if row_count > 10_000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="csv must have at most 10000 rows",
                )
    except csv.Error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid csv file")
    return raw, headers


@router.post("/datasets", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    dataset_name: str = Form(...),
    file: UploadFile = File(...),
    user_id: int = Form(...),
    session: AsyncSession = Depends(get_session),
    s3_client=Depends(get_s3_client),
):
    if not dataset_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="dataset_name must not be empty"
        )

    file_bytes, _ = await _validate_csv(file)
    key = f"datasets/{user_id}/{dataset_name}.csv"
    s3_path = f"s3://{settings.s3.bucket}/{key}"

    await s3_client.put_object(Bucket=settings.s3.bucket, Key=key, Body=file_bytes)

    dataset = Dataset(user_id=user_id, name=dataset_name, s3_path=s3_path)
    session.add(dataset)
    await session.commit()
    await session.refresh(dataset)
    return dataset


@router.get("/datasets", response_model=list[DatasetOut])
async def list_datasets(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.scalars(
        select(Dataset).where(Dataset.user_id == user_id).order_by(Dataset.created_at.desc())
    )
    return list(result.all())

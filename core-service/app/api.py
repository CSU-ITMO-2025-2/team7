import csv
import io

from confluent_kafka import KafkaException
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .clients import get_kafka_producer, get_s3_client, send_run_message
from .config import settings
from .database import get_session
from .models import Dataset, Run, RunStatus, User
from .security import create_access_token, get_current_user_id
from .schemas import (
    DatasetOut,
    RunCreate,
    RunOut,
    RunStatusUpdate,
    Token,
    UserCreate,
    UserOut,
)

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    hashed_password = pwd_context.hash(payload.password)
    user = User(login=payload.login, password_hash=hashed_password)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="login already exists")
    await session.refresh(user)
    return user


@router.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)
):
    user = await session.scalar(select(User).where(User.login == form_data.username))
    if user is None or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    token = create_access_token(user_id=user.id)
    return Token(access_token=token)


async def _validate_csv(file: UploadFile) -> tuple[bytes, list[str]]:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file is empty")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file must be utf-8 csv")

    stream = io.StringIO(text)
    try:
        reader = csv.reader(stream)
        headers = next(reader, None)
        if not headers or all(not header.strip() for header in headers):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="csv must contain header row"
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
                    status_code=status.HTTP_400_BAD_REQUEST, detail="csv must have at most 50 columns"
                )
            if row_count > 10_000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="csv must have at most 10000 rows"
                )
    except csv.Error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid csv file")
    return raw, headers


@router.post("/datasets", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    dataset_name: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    s3_client=Depends(get_s3_client),
    user_id: int = Depends(get_current_user_id),
):
    if not dataset_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="dataset_name must not be empty"
        )
    owner = await session.scalar(select(User).where(User.id == user_id))
    if owner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    file_bytes, _ = await _validate_csv(file)
    key = f"{user_id}/{dataset_name}/{dataset_name}.csv"
    s3_path = f"s3://{settings.s3_bucket}/{key}"

    await s3_client.put_object(Bucket=settings.s3_bucket, Key=key, Body=file_bytes)

    dataset = Dataset(user_id=user_id, name=dataset_name, s3_path=s3_path)
    session.add(dataset)
    await session.commit()
    await session.refresh(dataset)
    return dataset


@router.get("/datasets", response_model=list[DatasetOut])
async def list_datasets(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    result = await session.scalars(
        select(Dataset)
        .where(Dataset.user_id == user_id)
        .order_by(Dataset.created_at.desc())
    )
    return list(result.all())


@router.post("/runs", response_model=RunOut, status_code=status.HTTP_201_CREATED)
async def create_run(
    payload: RunCreate,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    dataset = await session.scalar(
        select(Dataset).where(
            Dataset.id == payload.dataset_id,
            Dataset.user_id == user_id,
        )
    )
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="dataset not found")

    run = Run(
        user_id=user_id,
        dataset_id=payload.dataset_id,
        status=RunStatus.IN_QUEUE,
        configuration=payload.configuration,
    )
    session.add(run)
    await session.flush()
    await session.refresh(run)

    producer = get_kafka_producer()
    message = {
        "user_id": user_id,
        "dataset_s3_path": dataset.s3_path,
        "run_id": run.id,
        "configuration": payload.configuration,
    }
    try:
        send_run_message(producer, message)
    except KafkaException as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"failed to publish run: {exc}",
        )

    await session.commit()
    await session.refresh(run)
    return run


@router.get("/runs", response_model=list[RunOut])
async def list_runs(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    result = await session.scalars(
        select(Run).where(Run.user_id == user_id).order_by(Run.created_at.desc())
    )
    return list(result.all())


@router.post("/runs/{run_id}/status", response_model=RunOut)
async def update_run_status(
    run_id: int,
    payload: RunStatusUpdate,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    run = await session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    if run.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    run.status = payload.status
    await session.commit()
    await session.refresh(run)
    return run

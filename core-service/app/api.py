from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_session
from .models import Run, RunStatus, User
from .security import create_access_token, get_current_user_id
from .schemas import (
    RunCreate,
    RunOut,
    Token,
    UserCreate,
    UserOut,
)

router = APIRouter()
pwd_hasher = PasswordHasher()


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    hashed_password = pwd_hasher.hash(payload.password)
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
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    try:
        pwd_hasher.verify(user.password_hash, form_data.password)
    except (VerifyMismatchError, VerificationError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    token = create_access_token(user_id=user.id)
    return Token(access_token=token)


@router.post("/runs", response_model=RunOut, status_code=status.HTTP_201_CREATED)
async def create_run(
    payload: RunCreate,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    run = Run(
        user_id=user_id,
        dataset_id=payload.dataset_id,
        status=RunStatus.IN_QUEUE,
        configuration=payload.configuration,
    )
    session.add(run)
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


@router.get("/runs/{run_id}", response_model=RunOut)
async def get_run(
    run_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    run = await session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    if run.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="access denied")
    return run



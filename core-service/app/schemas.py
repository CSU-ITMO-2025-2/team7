from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .models import RunStatus


class UserCreate(BaseModel):
    login: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=255)


class UserOut(BaseModel):
    id: int
    login: str
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetOut(BaseModel):
    id: int
    user_id: int
    name: str
    s3_path: str
    created_at: datetime

    class Config:
        from_attributes = True


class RunCreate(BaseModel):
    dataset_id: int
    configuration: dict[str, Any]


class RunOut(BaseModel):
    id: int
    user_id: int
    dataset_id: int
    status: RunStatus
    configuration: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class RunStatusUpdate(BaseModel):
    status: RunStatus


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

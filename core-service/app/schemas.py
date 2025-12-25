from datetime import datetime
from typing import Any

from pydantic import BaseModel

from .models import RunStatus


class UserCreate(BaseModel):
    login: str
    password: str


class UserOut(BaseModel):
    id: int
    login: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


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

from datetime import datetime

from pydantic import BaseModel


class DatasetOut(BaseModel):
    id: int
    user_id: int
    name: str
    s3_path: str
    created_at: datetime

    class Config:
        from_attributes = True


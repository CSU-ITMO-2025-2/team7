from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DatasetOut(BaseModel):
    id: int
    user_id: int
    name: str
    s3_path: str
    created_at: datetime

    class Config:
        from_attributes = True


class ColumnStats(BaseModel):
    name: str
    min: float
    max: float
    mean: float
    std: float


class Distribution(BaseModel):
    name: str
    bins: list[float]
    counts: list[int]


class DatasetStats(BaseModel):
    row_count: int
    column_count: int
    target_name: str
    columns: list[ColumnStats]
    distributions: list[Distribution] = Field(default_factory=list)


class ModelInfo(BaseModel):
    name: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class RunMetrics(BaseModel):
    train: dict[str, float]
    test: dict[str, float]


class RunResultsIn(BaseModel):
    dataset_name: str
    dataset_stats: DatasetStats
    model: ModelInfo
    metrics: RunMetrics


class RunFailureIn(BaseModel):
    error: str | None = None

import csv
import io

import httpx
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .clients import get_core_client, get_s3_client
from .config import settings
from .database import get_session
from .models import Dataset
from .schemas import DatasetOut, Distribution, RunFailureIn, RunResultsIn
from .security import get_current_user_id, oauth2_scheme

router = APIRouter()


def _format_float(value: float) -> str:
    return f"{value:.4f}"


def _build_bin_labels(bins: list[float], count: int) -> list[str]:
    if count <= 0:
        return []
    labels = [""] * count
    if len(bins) >= count + 1:
        for index in {0, count // 2, count - 1}:
            labels[index] = f"{bins[index]:.2f}"
    return labels


def _build_histogram(dist: Distribution, width: int = 420, height: int = 160) -> Drawing:
    counts = dist.counts or [0]
    drawing = Drawing(width, height)
    chart = VerticalBarChart()
    chart.x = 30
    chart.y = 20
    chart.height = height - 30
    chart.width = width - 40
    chart.data = [counts]
    chart.strokeColor = colors.black
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(counts) if counts else 1
    chart.valueAxis.valueStep = max(1, int(chart.valueAxis.valueMax / 4) or 1)
    chart.categoryAxis.categoryNames = _build_bin_labels(dist.bins, len(counts))
    chart.categoryAxis.labels.angle = 45
    chart.categoryAxis.labels.dy = -10
    chart.bars[0].fillColor = colors.HexColor("#4C8EDA")
    drawing.add(chart)
    return drawing


def _build_report_pdf(run_id: int, payload: RunResultsIn) -> bytes:
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story: list[object] = []

    story.append(Paragraph(f"Run Report #{run_id}", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Dataset", styles["Heading2"]))
    story.append(Paragraph(f"Name: {payload.dataset_name}", styles["Normal"]))
    story.append(
        Paragraph(
            f"Rows: {payload.dataset_stats.row_count} | Columns: {payload.dataset_stats.column_count}",
            styles["Normal"],
        )
    )
    story.append(Paragraph(f"Target: {payload.dataset_stats.target_name}", styles["Normal"]))
    story.append(Spacer(1, 10))

    column_table = [["Column", "Min", "Max", "Mean", "Std"]]
    for column in payload.dataset_stats.columns:
        column_table.append(
            [
                column.name,
                _format_float(column.min),
                _format_float(column.max),
                _format_float(column.mean),
                _format_float(column.std),
            ]
        )
    table = Table(column_table, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F4058")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D6DD")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(table)

    if payload.dataset_stats.distributions:
        story.append(Spacer(1, 14))
        story.append(Paragraph("Distributions", styles["Heading2"]))
        for dist in payload.dataset_stats.distributions:
            story.append(Paragraph(dist.name, styles["Heading3"]))
            story.append(_build_histogram(dist))
            story.append(Spacer(1, 10))

    story.append(Spacer(1, 14))
    story.append(Paragraph("Model", styles["Heading2"]))
    story.append(Paragraph(f"Name: {payload.model.name}", styles["Normal"]))
    if payload.model.parameters:
        params_table = [["Parameter", "Value"]]
        for name, value in payload.model.parameters.items():
            params_table.append([name, str(value)])
        param_table = Table(params_table, repeatRows=1)
        param_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F4058")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D6DD")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(param_table)
    else:
        story.append(Paragraph("Parameters: none", styles["Normal"]))

    story.append(Spacer(1, 14))
    story.append(Paragraph("Metrics", styles["Heading2"]))
    metrics_table = [["Split", "R2", "MSE"]]
    for split in ("train", "test"):
        values = getattr(payload.metrics, split)
        metrics_table.append(
            [
                split,
                _format_float(values.get("r2_score", 0.0)),
                _format_float(values.get("mean_squared_error", 0.0)),
            ]
        )
    metrics = Table(metrics_table, repeatRows=1)
    metrics.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F4058")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D6DD")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(metrics)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


async def _ensure_run_access(core_client: httpx.AsyncClient, run_id: int, token: str) -> None:
    try:
        response = await core_client.get(
            f"/runs/{run_id}", headers={"Authorization": f"Bearer {token}"}
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="failed to connect to core service",
        )

    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    if response.status_code == status.HTTP_403_FORBIDDEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="access denied")
    if not response.is_success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="failed to fetch run from core service",
        )


async def _set_run_status(
    core_client: httpx.AsyncClient, run_id: int, status_value: str, token: str
) -> None:
    try:
        response = await core_client.post(
            f"/runs/{run_id}/status",
            json={"status": status_value},
            headers={"Authorization": f"Bearer {token}"},
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="failed to connect to core service",
        )

    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    if response.status_code == status.HTTP_403_FORBIDDEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="access denied")
    if not response.is_success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="failed to update run status",
        )


async def _read_s3_object(s3_client, key: str) -> bytes:
    try:
        response = await s3_client.get_object(Bucket=settings.s3.bucket, Key=key)
        return await response["Body"].read()
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code in {"NoSuchKey", "404"}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="artifact not found")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="failed to fetch artifact from s3",
        ) from exc


def _artifact_key(run_id: int, name: str) -> str:
    return f"runs/{run_id}/{name}"


@router.get("/health")
async def health_check():
    return {"status": "ok"}


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
    user_id: int = Depends(get_current_user_id),
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
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    result = await session.scalars(
        select(Dataset).where(Dataset.user_id == user_id).order_by(Dataset.created_at.desc())
    )
    return list(result.all())


@router.post("/runs/{run_id}/results", status_code=status.HTTP_201_CREATED)
async def create_run_results(
    run_id: int,
    payload: RunResultsIn,
    token: str = Depends(oauth2_scheme),
    _: int = Depends(get_current_user_id),
    core_client: httpx.AsyncClient = Depends(get_core_client),
    s3_client=Depends(get_s3_client),
):
    await _ensure_run_access(core_client, run_id, token)
    key = _artifact_key(run_id, "results.pdf")
    try:
        pdf_bytes = _build_report_pdf(run_id, payload)
        await s3_client.put_object(
            Bucket=settings.s3.bucket,
            Key=key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
    except Exception:
        await _set_run_status(core_client, run_id, "failed", token)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to create run report",
        )

    await _set_run_status(core_client, run_id, "completed", token)
    s3_path = f"s3://{settings.s3.bucket}/{key}"
    return {"s3_path": s3_path}


@router.post("/runs/{run_id}/failed", status_code=status.HTTP_202_ACCEPTED)
async def mark_run_failed(
    run_id: int,
    payload: RunFailureIn,
    token: str = Depends(oauth2_scheme),
    _: int = Depends(get_current_user_id),
    core_client: httpx.AsyncClient = Depends(get_core_client),
):
    await _ensure_run_access(core_client, run_id, token)
    await _set_run_status(core_client, run_id, "failed", token)
    return {"status": "failed", "detail": payload.error}


@router.get("/runs/{run_id}/results")
async def download_run_results(
    run_id: int,
    token: str = Depends(oauth2_scheme),
    _: int = Depends(get_current_user_id),
    core_client: httpx.AsyncClient = Depends(get_core_client),
    s3_client=Depends(get_s3_client),
):
    await _ensure_run_access(core_client, run_id, token)
    key = _artifact_key(run_id, "results.pdf")
    body = await _read_s3_object(s3_client, key)
    filename = f"run-{run_id}-results.pdf"
    return Response(
        content=body,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/runs/{run_id}/model")
async def download_run_model(
    run_id: int,
    token: str = Depends(oauth2_scheme),
    _: int = Depends(get_current_user_id),
    core_client: httpx.AsyncClient = Depends(get_core_client),
    s3_client=Depends(get_s3_client),
):
    await _ensure_run_access(core_client, run_id, token)
    key = _artifact_key(run_id, "model.pkl")
    body = await _read_s3_object(s3_client, key)
    filename = f"run-{run_id}-model.pkl"
    return Response(
        content=body,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

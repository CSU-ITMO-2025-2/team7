import asyncio
import csv
import io
import json
import logging
import pickle
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

import aiobotocore.session
import httpx
import numpy as np
import uvicorn
from confluent_kafka import Consumer, KafkaError, KafkaException
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from .config import settings
from .model_specs import MODEL_SPECS, get_model_catalog

logger = logging.getLogger(__name__)
_s3_session = aiobotocore.session.get_session()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stop_event = asyncio.Event()
    consumer_task = asyncio.create_task(_consume(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        await consumer_task


app = FastAPI(title="Train Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/models")
async def list_models() -> dict[str, Any]:
    return get_model_catalog()


@dataclass
class RunMessage:
    user_id: int
    dataset_s3_path: str
    run_id: int
    configuration: dict[str, Any]


class InvalidModelParametersError(ValueError):
    pass


def _parse_message(raw: bytes) -> RunMessage:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("failed to decode kafka message") from exc

    try:
        configuration = payload.get("configuration") or {}
        if not isinstance(configuration, dict):
            raise TypeError("configuration must be a dict")
        return RunMessage(
            user_id=int(payload["user_id"]),
            dataset_s3_path=str(payload["dataset_s3_path"]),
            run_id=int(payload["run_id"]),
            configuration=configuration,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid kafka message payload") from exc


def _create_consumer() -> Consumer:
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka.bootstrap_servers,
            "group.id": settings.kafka.group_id,
            "enable.auto.commit": False,
            "auto.offset.reset": settings.kafka.auto_offset_reset,
        }
    )
    consumer.subscribe([settings.kafka.topic_name])
    return consumer


def _create_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.core_service.base_url,
        # timeout=httpx.Timeout(10, read=30),
    )


def _create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.core_service.jwt_expires_minutes
    )
    to_encode = {"user_id": user_id, "exp": expire}
    return jwt.encode(
        to_encode,
        settings.core_service.jwt_secret,
        algorithm=settings.core_service.jwt_algorithm,
    )


async def _update_run_status(
    client: httpx.AsyncClient, run_id: int, status: str, token: str
) -> None:
    print(f"Updating run {run_id} status to {status}")
    response = await client.post(
        f"/runs/{run_id}/status",
        json={"status": status},
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()


def _extract_s3_path(s3_path: str) -> tuple[str, str]:
    parsed = urlparse(s3_path)
    if parsed.scheme != "s3":
        raise ValueError("dataset path must start with s3://")
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    if not bucket or not key:
        raise ValueError("dataset s3 path is missing bucket or key")
    return bucket, key


async def _download_dataset(s3_path: str) -> bytes:
    bucket, key = _extract_s3_path(s3_path)
    print(
        "Downloading dataset from",
        bucket,
        key,
        settings.s3.access_key_id,
        settings.s3.secret_access_key,
    )
    async with _s3_session.create_client(
        "s3",
        endpoint_url=settings.s3.endpoint_url,
        aws_access_key_id=settings.s3.access_key_id,
        aws_secret_access_key=settings.s3.secret_access_key,
    ) as client:
        response = await client.get_object(Bucket=bucket, Key=key)
        body = await response["Body"].read()
    return body


def _load_arrays(raw: bytes) -> tuple[np.ndarray, np.ndarray]:
    stream = io.StringIO(raw.decode("utf-8"))
    reader = csv.DictReader(stream)
    if not reader.fieldnames:
        raise ValueError("csv file is missing header row")

    lower_to_name = {name.lower(): name for name in reader.fieldnames}
    target_column = lower_to_name.get("target")
    if target_column is None:
        raise ValueError("csv file must contain target column")

    feature_columns = [name for name in reader.fieldnames if name != target_column]
    if not feature_columns:
        raise ValueError("csv file must contain at least one feature column")

    X_rows: list[list[float]] = []
    y_rows: list[float] = []
    for row in reader:
        try:
            y_rows.append(float(row[target_column]))
            X_rows.append([float(row[column]) for column in feature_columns])
        except (TypeError, ValueError) as exc:
            raise ValueError("csv contains non-numeric values") from exc

    if not X_rows:
        raise ValueError("csv file does not contain any rows")

    return np.array(X_rows, dtype=float), np.array(y_rows, dtype=float)


def _extract_model_config(configuration: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if not configuration:
        return "LinearRegression", {}

    if "model" in configuration:
        model_name = configuration.get("model")
        if "hyperparameters" in configuration:
            hyperparameters = configuration.get("hyperparameters", {})
        else:
            hyperparameters = {k: v for k, v in configuration.items() if k != "model"}
    else:
        model_name = "LinearRegression"
        hyperparameters = configuration

    if not isinstance(model_name, str):
        raise InvalidModelParametersError("model must be a string")
    if hyperparameters is None:
        hyperparameters = {}
    if not isinstance(hyperparameters, dict):
        raise InvalidModelParametersError("hyperparameters must be a dict")

    return model_name, hyperparameters


def _coerce_param_value(param_name: str, param_spec: dict[str, Any], value: Any) -> Any:
    if value is None or value == "":
        if param_spec.get("nullable"):
            return None
        raise InvalidModelParametersError(f"missing value for {param_name}")

    param_type = param_spec.get("type")
    if param_type == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.lower()
            if lowered in ("true", "1", "yes"):
                return True
            if lowered in ("false", "0", "no"):
                return False
        raise InvalidModelParametersError(f"invalid boolean for {param_name}")
    if param_type == "int":
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise InvalidModelParametersError(f"invalid int for {param_name}") from exc
        return _validate_numeric(param_name, param_spec, parsed)
    if param_type == "float":
        try:
            parsed = float(value)
        except (TypeError, ValueError) as exc:
            raise InvalidModelParametersError(f"invalid float for {param_name}") from exc
        return _validate_numeric(param_name, param_spec, parsed)
    if param_type == "enum":
        options = param_spec.get("options", [])
        if value in options:
            return value
        raise InvalidModelParametersError(f"invalid option for {param_name}")
    return value


def _validate_numeric(param_name: str, param_spec: dict[str, Any], value: float) -> float:
    min_value = param_spec.get("min")
    if min_value is not None and value < min_value:
        raise InvalidModelParametersError(f"value for {param_name} is below minimum")
    max_value = param_spec.get("max")
    if max_value is not None and value > max_value:
        raise InvalidModelParametersError(f"value for {param_name} is above maximum")
    return value


def _build_model(configuration: dict[str, Any]) -> Any:
    model_name, hyperparameters = _extract_model_config(configuration)
    spec = MODEL_SPECS.get(model_name)
    if spec is None:
        raise InvalidModelParametersError(f"unsupported model: {model_name}")

    safe_params: dict[str, Any] = {}
    param_specs = spec["parameters"]
    unknown_params = set(hyperparameters) - set(param_specs)
    if unknown_params:
        unknown_list = ", ".join(sorted(unknown_params))
        raise InvalidModelParametersError(f"unsupported parameters: {unknown_list}")
    for param_name, value in hyperparameters.items():
        if param_name not in param_specs:
            continue
        safe_params[param_name] = _coerce_param_value(param_name, param_specs[param_name], value)
    return spec["class"](**safe_params)


def _evaluate_model(
    model: Any,
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
) -> dict[str, dict[str, float]]:
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    return {
        "train": {
            "r2_score": float(r2_score(y_train, train_pred)),
            "mean_squared_error": float(mean_squared_error(y_train, train_pred)),
        },
        "test": {
            "r2_score": float(r2_score(y_test, test_pred)),
            "mean_squared_error": float(mean_squared_error(y_test, test_pred)),
        },
    }


async def _upload_artifacts(run_id: int, model: Any, metrics: dict[str, Any]) -> None:
    model_key = f"runs/{run_id}/model.pkl"
    metrics_key = f"runs/{run_id}/metrics.json"
    async with _s3_session.create_client(
        "s3",
        endpoint_url=settings.s3.endpoint_url,
        aws_access_key_id=settings.s3.access_key_id,
        aws_secret_access_key=settings.s3.secret_access_key,
    ) as client:
        await client.put_object(
            Bucket=settings.s3.bucket,
            Key=model_key,
            Body=pickle.dumps(model),
        )
        await client.put_object(
            Bucket=settings.s3.bucket,
            Key=metrics_key,
            Body=json.dumps(metrics).encode("utf-8"),
        )


async def _process_message(message: RunMessage, http_client: httpx.AsyncClient) -> None:
    token = _create_access_token(message.user_id)
    print("user id:", message.user_id)
    await _update_run_status(http_client, message.run_id, "processing", token)
    try:
        model = _build_model(message.configuration)
        dataset_bytes = await _download_dataset(message.dataset_s3_path)
        X, y = _load_arrays(dataset_bytes)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model.fit(X_train, y_train)
        metrics = _evaluate_model(model, X_train, X_test, y_train, y_test)
        await _upload_artifacts(message.run_id, model, metrics)
        await _update_run_status(http_client, message.run_id, "completed", token)
        logger.info("run %s completed", message.run_id)
    except InvalidModelParametersError:
        logger.warning("invalid model parameters for run %s", message.run_id, exc_info=True)
        try:
            await _update_run_status(http_client, message.run_id, "failed", token)
        except Exception:
            logger.exception("failed to update run %s status to failed", message.run_id)
    except Exception:
        logger.exception("failed to process run %s", message.run_id)
        try:
            await _update_run_status(http_client, message.run_id, "failed", token)
        except Exception:
            logger.exception("failed to update run %s status to failed", message.run_id)


async def _consume(stop_event: asyncio.Event) -> None:
    consumer = _create_consumer()
    async with _create_http_client() as http_client:
        try:
            while not stop_event.is_set():
                msg = await asyncio.to_thread(consumer.poll, 1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error("kafka error: %s", msg.error())
                    continue

                try:
                    run_message = _parse_message(msg.value())
                except ValueError as exc:
                    logger.error("skipping invalid message: %s", exc)
                    consumer.commit(message=msg, asynchronous=False)
                    continue

                await _process_message(run_message, http_client)
                try:
                    consumer.commit(message=msg, asynchronous=False)
                except KafkaException as exc:
                    logger.error("failed to commit offset: %s", exc)
        finally:
            consumer.close()


def main() -> None:
    uvicorn.run(
        "src.main:app",
        host=settings.api.host,
        port=settings.api.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()

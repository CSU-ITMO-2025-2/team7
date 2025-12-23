"""
Обучение модели Random Forest для предсказания цен на недвижимость в Бостоне.
Метрики выводятся в реальном времени через DVCLive.
"""

import pickle
from pathlib import Path

import click
import numpy as np
import pandas as pd
from dvclive import Live
from loguru import logger
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import MODELS_DIR, RAW_DATA_DIR, HOUSING_DATA_FILE


def load_data(data_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    """Загрузка данных Boston Housing."""
    logger.info(f"Загрузка данных из {data_path}")

    # Чтение CSV без заголовков (данные разделены пробелами)
    df = pd.read_csv(data_path, sep=r"\s+", header=None)

    # Названия колонок
    column_names = [
        "CRIM",
        "ZN",
        "INDUS",
        "CHAS",
        "NOX",
        "RM",
        "AGE",
        "DIS",
        "RAD",
        "TAX",
        "PTRATIO",
        "B",
        "LSTAT",
        "MEDV",
    ]
    df.columns = column_names

    # Разделение на признаки и целевую переменную
    X = df.drop("MEDV", axis=1)
    y = df["MEDV"]

    logger.info(f"Загружено {len(df)} записей, {len(X.columns)} признаков")
    return X, y


def train_random_forest(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_estimators: int = 100,
    max_depth: int | None = None,
    min_samples_split: int = 2,
    min_samples_leaf: int = 1,
    random_state: int = 42,
) -> RandomForestRegressor:
    """Обучение модели Random Forest."""
    logger.info("Обучение модели Random Forest...")

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)
    logger.success("Модель обучена!")

    return model


def evaluate_model(
    model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series
) -> dict[str, float]:
    """Оценка модели и расчёт метрик."""
    y_pred = model.predict(X_test)

    metrics = {
        "r2_score": r2_score(y_test, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
        "mae": mean_absolute_error(y_test, y_pred),
        "mape": np.mean(np.abs((y_test - y_pred) / y_test)) * 100,
    }

    return metrics


@click.command()
@click.option(
    "--n-estimators", "-n", default=100, type=int, help="Количество деревьев в лесу"
)
@click.option(
    "--max-depth",
    "-d",
    default=10,
    type=int,
    help="Максимальная глубина деревьев (0 = без ограничений)",
)
@click.option(
    "--min-samples-split",
    "-s",
    default=5,
    type=int,
    help="Минимальное число образцов для разбиения узла",
)
@click.option(
    "--min-samples-leaf",
    "-l",
    default=2,
    type=int,
    help="Минимальное число образцов в листе",
)
@click.option(
    "--test-size",
    "-t",
    default=0.2,
    type=float,
    help="Доля данных для тестовой выборки (0.0-1.0)",
)
@click.option(
    "--random-state", "-r", default=42, type=int, help="Seed для воспроизводимости"
)
@click.option(
    "--data-path",
    default=None,
    type=click.Path(exists=False),
    help="Путь к файлу данных (по умолчанию: data/raw/housing.csv)",
)
def main(
    n_estimators: int,
    max_depth: int,
    min_samples_split: int,
    min_samples_leaf: int,
    test_size: float,
    random_state: int,
    data_path: str | None,
):
    """Обучение модели Random Forest на данных Boston Housing."""

    # Обработка max_depth: 0 означает None (без ограничений)
    actual_max_depth = None if max_depth == 0 else max_depth

    # Параметры модели
    params = {
        "n_estimators": n_estimators,
        "max_depth": actual_max_depth,
        "min_samples_split": min_samples_split,
        "min_samples_leaf": min_samples_leaf,
        "random_state": random_state,
        "test_size": test_size,
    }

    # Путь к данным
    if data_path:
        data_file = Path(data_path)
    else:
        data_file = RAW_DATA_DIR / HOUSING_DATA_FILE

    if not data_file.exists():
        logger.error(f"Файл данных не найден: {data_file}")
        logger.info("Выполните 'dvc pull' для загрузки данных из MinIO")
        raise click.Abort()

    # DVCLive для логирования метрик в реальном времени
    with Live(save_dvc_exp=True) as live:
        # Логируем параметры
        for param_name, param_value in params.items():
            live.log_param(param_name, param_value)

        # Загрузка данных
        X, y = load_data(data_file)
        live.log_param("n_samples", len(X))
        live.log_param("n_features", len(X.columns))

        # Разделение на train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=params["test_size"], random_state=params["random_state"]
        )

        live.log_param("train_size", len(X_train))
        live.log_param("test_size_actual", len(X_test))

        # Обучение модели
        model = train_random_forest(
            X_train,
            y_train,
            n_estimators=params["n_estimators"],
            max_depth=params["max_depth"],
            min_samples_split=params["min_samples_split"],
            min_samples_leaf=params["min_samples_leaf"],
            random_state=params["random_state"],
        )

        # Оценка модели
        metrics = evaluate_model(model, X_test, y_test)

        # Логирование метрик через DVCLive
        for metric_name, metric_value in metrics.items():
            live.log_metric(metric_name, metric_value)
            logger.info(f"{metric_name}: {metric_value:.4f}")

        # Важность признаков
        feature_importance = pd.DataFrame(
            {"feature": X.columns, "importance": model.feature_importances_}
        ).sort_values("importance", ascending=False)

        logger.info("\n📊 Важность признаков:")
        for _, row in feature_importance.head(5).iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")

        # Сохранение модели
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        model_path = MODELS_DIR / "random_forest.pkl"

        with open(model_path, "wb") as f:
            pickle.dump(model, f)

        logger.success(f"Модель сохранена: {model_path}")

        # Логируем артефакт модели
        live.log_artifact(str(model_path), type="model", name="random_forest")

        # Итоговые метрики
        logger.info("\n" + "=" * 50)
        logger.info("📈 ИТОГОВЫЕ МЕТРИКИ:")
        logger.info(f"  R² Score:  {metrics['r2_score']:.4f}")
        logger.info(f"  RMSE:      {metrics['rmse']:.4f}")
        logger.info(f"  MAE:       {metrics['mae']:.4f}")
        logger.info(f"  MAPE:      {metrics['mape']:.2f}%")
        logger.info("=" * 50)


if __name__ == "__main__":
    main()

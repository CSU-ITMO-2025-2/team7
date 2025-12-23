# Boston Housing ML Application
# Dockerfile для запуска экспериментов по обучению модели

FROM python:3.13-slim

# Метаданные
LABEL maintainer="Boston Housing ML Project"
LABEL description="ML application для обучения и оценки моделей Boston Housing"

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Установка uv (современный менеджер пакетов Python)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Рабочая директория
WORKDIR /app

# Копирование файлов зависимостей
COPY pyproject.toml uv.lock ./

# Установка зависимостей (без dev-зависимостей для продакшн)
RUN uv sync --frozen --no-dev

# Копирование исходного кода
COPY src/ ./src/

# Создание директорий для данных и результатов
# Данные монтируются при запуске через docker-compose volumes
RUN mkdir -p data/raw data/models data/experiments dvclive

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Точка входа по умолчанию — обучение модели
ENTRYPOINT ["uv", "run", "python", "src/modeling/train.py"]

# Параметры по умолчанию (можно переопределить при запуске)
CMD ["--n-estimators", "100", "--max-depth", "10"]


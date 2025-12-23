# MinIO Object Storage для ML проекта Boston Housing
# Используется для хранения данных, моделей и артефактов

FROM minio/minio:latest

# Метаданные образа
LABEL maintainer="Boston Housing ML Project"
LABEL description="MinIO storage для хранения ML артефактов"

# Переменные окружения для доступа
ENV MINIO_ROOT_USER=minioadmin0
ENV MINIO_ROOT_PASSWORD=minioadmin1230

# Переменные для консоли
ENV MINIO_CONSOLE_ADDRESS=":9001"

# Порты
# 9000 - API порт для S3-совместимого доступа
# 9001 - Веб-консоль MinIO
EXPOSE 9000 9001

# Создаём директорию для данных
VOLUME ["/data"]

# Healthcheck для проверки работоспособности
HEALTHCHECK --interval=30s --timeout=20s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9000/minio/health/live || exit 1

# Запуск MinIO сервера
CMD ["server", "/data", "--console-address", ":9001"]


#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="$(pwd)/minio-data"

mkdir -p "$DATA_DIR"

docker run \
  --name minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=admin123 \
  -v "$DATA_DIR":/data \
  quay.io/minio/minio server /data --console-address ":9001"

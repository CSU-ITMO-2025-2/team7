FROM python:3.13-slim

WORKDIR /

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

CMD ["uv", "run", "python", "-m", "src.main"]

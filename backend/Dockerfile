# Build context is the repo root (pyproject.toml and uv.lock live there):
#   docker build -f backend/Dockerfile .
FROM ghcr.io/astral-sh/uv:0.9 AS uv

FROM public.ecr.aws/docker/library/python:3.13-slim AS build
COPY --from=uv /uv /bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM public.ecr.aws/docker/library/python:3.13-slim
# Lambda Web Adapter: proxies Lambda invocations to the HTTP server on $PORT
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:1.0.0 /lambda-adapter /opt/extensions/lambda-adapter
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY backend/src backend/src
COPY backend/models.yaml backend/models.yaml
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app/backend/src \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    AWS_LWA_PORT=8080 \
    AWS_LWA_READINESS_CHECK_PATH=/health \
    LITELLM_LOCAL_MODEL_COST_MAP=True
EXPOSE 8080
CMD ["uvicorn", "thirsty_tokens.app:app", "--host", "0.0.0.0", "--port", "8080"]

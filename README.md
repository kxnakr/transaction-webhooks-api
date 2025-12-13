# Transaction Webhooks API

FastAPI service that accepts transaction webhooks and enqueues background processing via Celery using Upstash Redis.

## Setup (uv)

1. Create `.env` from the template:

   `cp .env.example .env`

2. Fill in:
   - `DATABASE_URL`
   - `UPSTASH_REDIS_HOST`
   - `UPSTASH_REDIS_PORT`
   - `UPSTASH_REDIS_PASSWORD`

3. Install dependencies:

   `uv sync`

## Run locally

- API:
  `uv run uvicorn src.app:app --reload --port 8000`

- Worker:
  `uv run celery -A src.celery_app worker --loglevel=info --concurrency=4`

## Upstash Redis TLS

The app builds a TLS Redis URL (`rediss://`) from the Upstash env vars and enforces certificate validation with `ssl_cert_reqs=required`.

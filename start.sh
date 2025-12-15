#!/bin/bash
set -e

if [ "$SERVICE_TYPE" = "worker" ]; then
    echo "Starting Celery worker..."
    exec celery -A src.celery_app worker --loglevel=info --concurrency=4 --pool=prefork --max-tasks-per-child=100
else
    echo "Starting web server..."
    # With 2 vCPU, use 2 workers for better throughput without starving Celery.
    exec uvicorn src.app:app --host 0.0.0.0 --port ${PORT} --workers 2 --log-level info
fi

web: uvicorn src.app:app --host 0.0.0.0 --port $PORT --workers 2 --log-level info
worker: celery -A src.celery_app worker --loglevel=info --concurrency=4 --pool=prefork --max-tasks-per-child=100

from celery import Celery
from .config import settings


def make_celery() -> Celery:
    """Create and configure Celery application."""
    celery_app = Celery(
        settings.APP_NAME,
        broker=settings.UPSTASH_REDIS_CONNECTION_LINK,
        backend=settings.UPSTASH_REDIS_CONNECTION_LINK,
        include=["src.tasks"],
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_default_queue="transactions",
        task_routes={
            "src.tasks.process_transaction": {
                "queue": "transactions"
            },
        },
        result_expires=3600,
        result_persistent=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        broker_pool_limit=2,
        broker_heartbeat=30,
        task_default_max_retries=3,
        task_default_retry_delay=60,
        broker_connection_retry_on_startup=True,
        redis_socket_keepalive=True,
        redis_socket_keepalive_options={
            "TCP_KEEPIDLE": 60,
            "TCP_KEEPINTVL": 10,
            "TCP_KEEPCNT": 3,
        },
    )

    return celery_app


celery = make_celery()

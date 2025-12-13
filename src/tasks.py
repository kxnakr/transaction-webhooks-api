import logging
import time
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy import update

from .celery_app import celery
from .database import FAILED, PROCESSED, SessionLocal, Transaction, utc_now


logger = logging.getLogger(__name__)


@celery.task(
    name="src.tasks.process_transaction",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_transaction(self, transaction_id: str):
    """Process a transaction with 30-second simulation."""
    db = SessionLocal()
    try:
        logger.info("[%s] Starting 30-second processing...", transaction_id)
        time.sleep(30)
        logger.info("[%s] Processing complete!", transaction_id)

        processed_at = utc_now()

        stmt = (
            update(Transaction)
            .where(Transaction.transaction_id == transaction_id)
            .values(
                status=PROCESSED,
                processed_at=processed_at,
            )
        )

        db.execute(stmt)
        db.commit()

        return {
            "transaction_id": transaction_id,
            "status": PROCESSED,
            "processed_at": processed_at.isoformat(),
        }

    except Exception as exc:
        db.rollback()
        try:
            raise self.retry(exc=exc, countdown=60)
        except MaxRetriesExceededError:
            logger.exception(
                "[%s] Max retries exhausted; marking transaction as FAILED",
                transaction_id,
            )
            failed_at = utc_now()
            fail_stmt = (
                update(Transaction)
                .where(Transaction.transaction_id == transaction_id)
                .values(status=FAILED, processed_at=failed_at)
            )
            db.execute(fail_stmt)
            db.commit()
            raise

    finally:
        db.close()

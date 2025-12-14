import logging
import uvicorn
import time
from datetime import datetime
from typing import Optional, Union
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .tasks import process_transaction
from .database import (
    PROCESSING,
    Transaction,
    get_db,
    upsert_transaction,
    utc_now,
)


# Ensure our INFO logs actually emit even when uvicorn doesn't touch root logger.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("transactions.api")
logger.setLevel(logging.INFO)


def _normalize_datetime(value: Optional[Union[datetime, str]]) -> Optional[datetime]:
    """Handle non-ISO db datetime strings (e.g., `2025-12-14 19:59:25.47352+00`)."""
    if value is None or isinstance(value, datetime):
        return value

    # Convert Postgres-style string to ISO so pydantic can parse it.
    cleaned = value.strip().replace(" ", "T")
    if cleaned.endswith("+00"):
        cleaned = f"{cleaned}:00"

    return datetime.fromisoformat(cleaned)


class TransactionWebhook(BaseModel):
    """Webhook payload schema."""
    transaction_id: str = Field(..., alias="transaction_id")
    source_account: str
    destination_account: str
    amount: float
    currency: str

    class Config:
        populate_by_name = True


class TransactionResponse(BaseModel):
    """Transaction response schema."""

    transaction_id: str
    source_account: str
    destination_account: str
    amount: float
    currency: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime]


app = FastAPI(
    title="Transaction Webhooks API",
    version="1.0.0",
    docs_url="/docs",
)

@app.get("/", status_code=status.HTTP_202_ACCEPTED)
def root():
    """Health check endpoint."""
    return {
        "status": "HEALTHY",
        "current_time": utc_now()
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
    }


@app.post("/v1/webhooks/transactions", status_code=status.HTTP_202_ACCEPTED)
def accept_transaction(
    webhook: TransactionWebhook,
    db: Session = Depends(get_db),
):
    """Accept transaction webhook and queue for processing."""
    # Insert if new; do nothing if already present
    db_start = time.perf_counter()
    inserted = upsert_transaction(
        db=db,
        transaction_id=webhook.transaction_id,
        source_account=webhook.source_account,
        destination_account=webhook.destination_account,
        amount=webhook.amount,
        currency=webhook.currency,
    )
    db_ms = (time.perf_counter() - db_start) * 1000

    enqueue_ms = 0.0
    if inserted:
        # Queue background task (non-blocking) only for new records
        enqueue_start = time.perf_counter()
        try:
            process_transaction.apply_async(
                args=[webhook.transaction_id],
                task_id=f"transaction-{webhook.transaction_id}",
            )
        except Exception as exc:
            logger.exception(
                "Failed to enqueue transaction %s for processing",
                webhook.transaction_id,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to queue transaction for processing. Try again later.",
            ) from exc

        enqueue_ms = (time.perf_counter() - enqueue_start) * 1000

    logger.info(
        "[%s] accepted webhook; db=%.1fms enqueue=%.1fms queued=%s",
        webhook.transaction_id,
        db_ms,
        enqueue_ms,
        inserted,
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "transaction_id": webhook.transaction_id,
            "status": PROCESSING if inserted else "DUPLICATE",
            "queued": inserted,
        },
    )


@app.get(
    "/v1/transactions/{transaction_id}",
    response_model=list[TransactionResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
def transaction_status(
    transaction_id: str,
    db: Session = Depends(get_db),
):
    """Get transaction details by ID."""
    transaction = (
        db.query(Transaction)
        .filter(Transaction.transaction_id == transaction_id)
        .first()
    )

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return [TransactionResponse(
        transaction_id=transaction.transaction_id,
        source_account=transaction.source_account,
        destination_account=transaction.destination_account,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status,
        created_at=_normalize_datetime(transaction.created_at),
        processed_at=_normalize_datetime(transaction.processed_at),
    )]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

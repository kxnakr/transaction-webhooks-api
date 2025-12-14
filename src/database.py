from datetime import datetime, timezone
from sqlalchemy import (
    create_engine,
    Column,
    String,
    DateTime,
    Index,
    Numeric,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import insert

from .config import settings


# Database engine configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=False,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Constants
PROCESSING = "PROCESSING"
PROCESSED = "PROCESSED"
FAILED = "FAILED"


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class Transaction(Base):
    """Transaction model matching PostgreSQL schema."""

    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True, index=True)
    source_account = Column(String, nullable=False)
    destination_account = Column(String, nullable=False)
    amount = Column(Numeric(20, 2), nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_transactions_status", "status"),
        Index("idx_transactions_status_created", "status", "created_at"),
        Index("idx_transactions_created_at", created_at.desc()),
    )


def get_db():
    """Dependency for FastAPI to get database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def upsert_transaction(
    db,
    transaction_id: str,
    source_account: str,
    destination_account: str,
    amount: float,
    currency: str,
) -> bool:
    """Insert transaction; no-op on conflict. Returns True if inserted."""
    stmt = insert(Transaction).values(
        transaction_id=transaction_id,
        source_account=source_account,
        destination_account=destination_account,
        amount=amount,
        currency=currency,
        status=PROCESSING,
        created_at=utc_now(),
        processed_at=None,
    )

    stmt = stmt.on_conflict_do_nothing(index_elements=["transaction_id"])

    result = db.execute(stmt)
    db.commit()
    return result.rowcount > 0

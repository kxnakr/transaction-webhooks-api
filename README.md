# Transaction Webhooks API

**Live API:** https://wfg-transaction-webhooks-api-beb98995ae5e.herokuapp.com

**API Documentation:** https://wfg-transaction-webhooks-api-beb98995ae5e.herokuapp.com/docs

FastAPI service that accepts transaction webhooks from payment processors (like RazorPay) and processes them reliably in the background using Celery.


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

Open 2 terminal and both of these:

- API:
  `uv run uvicorn src.app:app --reload --port 8000`

- Worker:
  `uv run celery -A src.celery_app worker --loglevel=info --concurrency=4`

## Architecture & Technical Choices

### Why FastAPI?
- **Auto OpenAPI Docs:** /docs endpoint for easy testing (as requested)
- **Type Safety:** Pydantic models for request/response validation
- **Developer Experience:** Minimal boilerplate with intuitive syntax

### Why Celery + Redis?
- **Reliable Background Processing:** Separate webhook acceptance from heavy processing
- **Task Retries:** 3 automatic retries with 60s delays for reliability
- **Task Acknowledgment:** Tasks only acknowledged after successful completion (`task_acks_late=True`)
- **Scalability:** Can add more workers independently of API servers

### Why Upstash Redis?
- **Serverless:** Pay-per-request, no idle costs
- **TLS Encryption:** Secure message broker with certificate validation
- **Low Latency:** Fast task queueing for webhook acknowledgment

### Idempotency Strategy
Using PostgreSQL's `ON CONFLICT DO UPDATE` with conditional logic:
- If transaction already PROCESSED → preserve PROCESSED status
- If transaction is PROCESSING → return 202 without requeuing
- Database-level constraint ensures no duplicates even under race conditions

### Performance Optimizations
1. **Non-blocking Task Queue:** `apply_async()` returns immediately
2. **Connection Pooling:** 10 pool size + 20 overflow prevents connection overhead
3. **Indexes:** On status, (status + created_at), and created_at DESC
4. **Async Endpoints:** All routes use async handlers for concurrent request handling

## Testing the API

### Using the Deployed API

All examples use the live API: `https://wfg-transaction-webhooks-api-beb98995ae5e.herokuapp.com`

#### 1. Health Check
```bash
curl https://wfg-transaction-webhooks-api-beb98995ae5e.herokuapp.com/
```

**Expected Response:**
```json
{
  "status": "HEALTHY",
  "current_time": "2025-12-13T21:12:27Z"
}
```

#### 2. Send a Transaction Webhook
```bash
curl -X POST https://wfg-transaction-webhooks-api-beb98995ae5e.herokuapp.com/v1/webhooks/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_test_001",
    "source_account": "acc_user_789",
    "destination_account": "acc_merchant_456",
    "amount": 1500,
    "currency": "INR"
  }'
```

**Expected Response (202 Accepted):**
```json
{
  "transaction_id": "txn_test_001",
  "status": "PROCESSING"
}
```

#### 3. Check Transaction Status (Immediately)
```bash
curl https://wfg-transaction-webhooks-api-beb98995ae5e.herokuapp.com/v1/transactions/txn_test_001
```

**Expected Response (while processing):**
```json
[{
  "transaction_id": "txn_test_001",
  "source_account": "acc_user_789",
  "destination_account": "acc_merchant_456",
  "amount": 1500,
  "currency": "INR",
  "status": "PROCESSING",
  "created_at": "2025-12-13T21:12:27Z",
  "processed_at": null
}]
```

#### 4. Wait 30 Seconds, Then Check Again
```bash
# Wait ~30 seconds for background processing to complete
sleep 30

curl https://wfg-transaction-webhooks-api-beb98995ae5e.herokuapp.com/v1/transactions/txn_test_001
```

**Expected Response (after processing):**
```json
[{
  "transaction_id": "txn_test_001",
  "source_account": "acc_user_789",
  "destination_account": "acc_merchant_456",
  "amount": 1500,
  "currency": "INR",
  "status": "PROCESSED",
  "created_at": "2025-12-13T21:12:27Z",
  "processed_at": "2025-12-13T21:12:57Z"
}]
```

#### 5. Test Idempotency (Send Same Webhook Again)
```bash
curl -X POST https://wfg-transaction-webhooks-api-beb98995ae5e.herokuapp.com/v1/webhooks/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_test_001",
    "source_account": "acc_user_789",
    "destination_account": "acc_merchant_456",
    "amount": 1500,
    "currency": "INR"
  }'
```

**Expected Response (202 Accepted, no duplicate processing):**
```json
{
  "transaction_id": "txn_test_001",
  "status": "PROCESSED",
  "message": "Already processed;"
}
```

### Using Swagger UI (Interactive Testing)

Visit https://wfg-transaction-webhooks-api-beb98995ae5e.herokuapp.com/docs for interactive API testing with auto-generated forms.

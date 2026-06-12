# Coffee Card API

FastAPI backend for the Coffee Card concession kiosk. See the [root README](../README.md) for the overall architecture, data models, and API endpoints.

## Stack

| Component  | Choice           | Notes                                          |
| ---------- | ---------------- | ---------------------------------------------- |
| Language   | Python 3.12      |                                                |
| Framework  | FastAPI 0.115    | Sync handlers; auto-generated OpenAPI docs     |
| Validation | Pydantic v2      | Request/response schemas and settings          |
| Database   | DynamoDB         | Single-table design, boto3                     |
| Runtime    | AWS Lambda       | Mangum ASGI adapter + Lambda Web Adapter       |
| Container  | python:3.12-slim | Multi-stage Dockerfile, builder → slim runtime |
| Local DB   | DynamoDB Local   | amazon/dynamodb-local, in-memory               |

## Project Layout

```text
api/
├── app/
│   ├── main.py           # FastAPI app - CORS, logging, router registration
│   ├── database.py       # CoffeeCardRepository, _get_table (lru_cache), get_repository dep
│   ├── models.py         # Pydantic models: Customer, Card - to_item/from_item for DynamoDB
│   ├── middlewares.py    # RequestLoggingMiddleware (correlation ID, duration)
│   ├── logging_config.py # Configures text vs JSON logging based on settings
│   ├── schemas.py        # Request/response schemas separate from DB models
│   ├── settings.py       # LocalSettings and ProdSettings (env-driven)
│   └── routers/
│       ├── customers.py  # Customer CRUD endpoints
│       ├── cards.py      # Card endpoints nested under /customers
│       └── health.py     # GET /health - DynamoDB describe_table connectivity check
├── handler.py            # Mangum entry point for AWS Lambda
├── seed.py               # Idempotent local dev seed (Alice + Bob + 3 cards)
├── tests/
│   ├── conftest.py       # moto DynamoDB fixture, async HTTP client, model factories
│   ├── test_customers.py # Tests for /customers endpoints
│   ├── test_cards.py     # Tests for /customers/{id}/cards endpoints
│   └── test_health.py    # Tests for /health endpoint
├── Dockerfile
├── requirements.txt
└── requirements-dev.txt  # pytest, pytest-asyncio, httpx, moto[dynamodb]
```

## Local Development Setup

Create a virtual environment so your IDE can resolve imports:

```bash
cd api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

In VS Code: `Cmd+Shift+P` → **Python: Select Interpreter** → pick `api/.venv/bin/python`.

## Running Locally

**Prerequisites:** Docker + Docker Compose.

```bash
# From the repo root - starts DynamoDB Local, creates the table, builds and starts the API
make dev
```

This runs `docker compose up -d --build` then starts the Vite dev server.

```bash
# Seed sample data (idempotent, safe to re-run)
make seed
```

The API is available at `http://localhost:8000`.
OpenAPI docs: `http://localhost:8000/docs`.

### Verify

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/customers/11111111-1111-1111-1111-111111111111
```

## Running Tests

Tests use [moto](https://docs.getmoto.org/) to mock DynamoDB - no database or Docker required.

```bash
cd api
pytest
```

```bash
# Verbose
pytest -v

# Single file or class
pytest tests/test_cards.py
pytest tests/test_customers.py::TestUpdateCustomer
```

## Key Decisions

### Single-table DynamoDB design

All records live in one table. Customers and their cards share the same partition key (`PK = CUSTOMER#{id}`), with cards distinguished by sort key (`SK = CARD#{card_id}`). A single `Query` on the PK returns a customer and all their cards in one round trip.

### Atomic redeem/refund via ConditionExpression

`redeem` and `refund` use DynamoDB `UpdateItem` with a `ConditionExpression` (`credits_used < total_credits` and `credits_used > 0` respectively). This makes the guard and the write atomic, preventing over-redemption under concurrent requests. A failed condition raises `ConditionalCheckFailedException`, mapped to HTTP 409.

### Settings: LocalSettings vs ProdSettings

`get_settings()` branches on `APP_ENV`:

- `local` → `LocalSettings`: reads a `.env` file via pydantic-settings.
- `prod` → `ProdSettings`: reads from Lambda environment variables; defaults `log_format` to `json` for CloudWatch.

### `is_archived` soft-delete

Both customers and cards use `is_archived` for soft-deletes rather than physical deletion. Archived records are excluded by default and can be restored via `PATCH` with `{ "is_archived": false }`.

### Seed is idempotent

`seed.py` checks for Alice's fixed UUID before inserting. Fixed UUIDs give stable IDs for curl commands and manual testing without having to look anything up.

## Environment Variables

| Variable                | Default                       | Notes                                       |
| ----------------------- | ----------------------------- | ------------------------------------------- |
| `APP_ENV`               | -                             | Required. `local` or `prod`                 |
| `APP_VERSION`           | `0.1.0`                       | Reported by `/api/health`                   |
| `LOG_LEVEL`             | `INFO`                        | Python logging level                        |
| `LOG_FORMAT`            | `text` (local), `json` (prod) | `json` emits structured logs for CloudWatch |
| `TABLE_NAME`            | `coffee-cards`                | DynamoDB table name                         |
| `AWS_REGION`            | `ap-southeast-2`              |                                             |
| `DYNAMODB_ENDPOINT_URL` | -                             | Set to `http://dynamodb:8000` for local     |
| `CORS_ORIGINS`          | `http://localhost:5173`       | Comma-separated list in prod                |

For local development these are already set in the root [docker-compose.yml](../docker-compose.yml); in prod they're set as Lambda environment variables via Terraform.

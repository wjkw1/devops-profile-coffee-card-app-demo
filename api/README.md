# Coffee Card API

FastAPI backend for the Coffee Card concession kiosk.

## Stack

| Component  | Choice                 | Notes                                          |
| ---------- | ---------------------- | ---------------------------------------------- |
| Language   | Python 3.12            |                                                |
| Framework  | FastAPI 0.115          | Async by default, auto-generated OpenAPI docs  |
| Validation | Pydantic v2            | Request/response schemas, `EmailStr` built in  |
| ORM        | SQLAlchemy 2.0 (async) | New 2.0 mapped_column style throughout         |
| Migrations | Alembic                | Async runner via `asyncio.run` in `env.py`     |
| Database   | PostgreSQL 16          | `asyncpg` driver                               |
| Container  | python:3.12-slim       | Multi-stage Dockerfile, builder → slim runtime |

## Project Layout

```text
api/
├── app/
│   ├── main.py           # FastAPI app — includes routers
│   ├── database.py       # Async engine, session factory, get_session dep
│   ├── models.py         # SQLAlchemy ORM: Customer, Card
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── settings.py       # Pydantic settings loaded from .env
│   └── routers/
│       ├── customers.py  # Customer CRUD endpoints
│       ├── cards.py      # Card endpoints nested under /customers
│       └── health.py     # GET /health
├── alembic/
│   ├── env.py            # Async Alembic runner, reads DATABASE_URL from env
│   ├── script.py.mako    # Template for generated migration files
│   └── versions/
│       └── 001_initial_schema.py  # customers + cards tables
├── alembic.ini
├── seed.py               # Idempotent local dev seed (Alice + Bob + 3 cards)
├── tests/
│   ├── conftest.py       # Fixtures: mock session, async HTTP client, model factories
│   ├── test_customers.py # Unit tests for /customers endpoints
│   └── test_cards.py     # Unit tests for /customers/{id}/cards endpoints
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt  # Test dependencies (pytest, pytest-asyncio, httpx)
└── .env.example
```

## Local Development Setup (IntelliSense / IDE)

Create a virtual environment inside the `api/` directory so VS Code and other editors can resolve imports:

```bash
cd api
python3 -m venv .venv
source .venv/bin/activate
.venv/bin/pip install -r requirements.txt
```

Then in VS Code, open the Command Palette (`Cmd+Shift+P`) → **Python: Select Interpreter** → pick `api/.venv/bin/python`.

The `.venv` directory is already in `.gitignore`.

## Linting

Ruff is used for both linting and formatting. It runs automatically on commit via pre-commit.

### Install pre-commit hooks

From the **repo root** (not `api/`):

```bash
pip install pre-commit
pre-commit install
```

This installs hooks that run `ruff` (lint + autofix) and `ruff-format` on every `git commit`.

### Run manually

```bash
# Check all files
pre-commit run --all-files

# Ruff only
pre-commit run ruff --all-files
pre-commit run ruff-format --all-files
```

## Running Locally

**Prerequisites:** Docker + Docker Compose.

```bash
# From the repo root — builds the image, starts DB, runs migrations on boot
docker compose up --build

# Seed sample data (idempotent, safe to re-run)
docker compose --profile seed run --rm seed
```

The API will be available at `http://localhost:8000`.

OpenAPI docs are auto-generated at `http://localhost:8000/docs`.

### Verify

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/customers/11111111-1111-1111-1111-111111111111
```

## Running Tests

Tests are unit tests — no database or Docker required. The SQLAlchemy session is mocked, so they run entirely in-process.

Install test dependencies into your virtual environment (activate it first if you haven't already):

```bash
pip install -r requirements-dev.txt
```

Run all tests from the `api/` directory:

```bash
pytest
```

Run with verbose output to see each test name:

```bash
pytest -v
```

Run a single test file or class:

```bash
pytest tests/test_cards.py
pytest tests/test_customers.py::TestUpdateCustomer
```

## Implemented Endpoints

### Customers

| Method | Path                           | Status | Notes                                                      |
| ------ | ------------------------------ | ------ | ---------------------------------------------------------- |
| GET    | `/api/customers`               | Done   | `?search=` partial name match; `?include=archived` for all |
| POST   | `/api/customers`               | Done   | Body: `{ name, email? }`                                   |
| GET    | `/api/customers/{customer_id}` | Done   |                                                            |
| PATCH  | `/api/customers/{customer_id}` | Done   | Updates name, email, or `is_archived`                      |
| DELETE | `/api/customers/{customer_id}` | Done   | Soft-archives; returns updated customer                    |

### Cards

| Method | Path                                           | Status | Notes                                   |
| ------ | ---------------------------------------------- | ------ | --------------------------------------- |
| GET    | `/api/customers/{customer_id}/cards`           | Done   | `?include=archived` to include archived |
| POST   | `/api/customers/{customer_id}/cards`           | Done   | Creates card with 5 credits             |
| PATCH  | `/api/customers/{customer_id}/cards/{card_id}` | Done   | Updates `is_archived`                   |
| DELETE | `/api/customers/{customer_id}/cards/{card_id}` | Done   | Soft-delete via `is_archived`           |

### Actions

| Method | Path                                                  | Status | Notes                          |
| ------ | ----------------------------------------------------- | ------ | ------------------------------ |
| POST   | `/api/customers/{customer_id}/cards/{card_id}/redeem` | Done   | Increments `credits_used` by 1 |
| POST   | `/api/customers/{customer_id}/cards/{card_id}/refund` | Done   | Decrements `credits_used` by 1 |

### Health

| Method | Path          | Status | Notes                                                   |
| ------ | ------------- | ------ | ------------------------------------------------------- |
| GET    | `/api/health` | Done   | Returns `version`, `uptime_seconds`, `database` status  |

## Key Decisions

### `/api` route prefix

All routers are mounted with `prefix="/api"` in `main.py`. Individual routers remain unaware of the prefix — it is applied at registration, not inside the router file, making it straightforward to change (e.g. to `/v2`) without touching router files.

### Migrations run on container boot

The `api` service entrypoint runs `alembic upgrade head` before starting uvicorn. This means the schema is always in sync with the code on startup — no separate migration step required in local dev or in ECS task launches. The trade-off is that boot is slightly slower; acceptable for this scale.

### Async Alembic via `asyncio.run`

Alembic is inherently synchronous, but `asyncpg` doesn't provide a sync driver. `alembic/env.py` wraps the migration runner in `asyncio.run(run_async_migrations())` using `async_engine_from_config` with `pool.NullPool`. This is the Alembic-recommended pattern for async drivers.

### Seed is profile-gated

The `seed` service in `docker-compose.yml` uses `profiles: [seed]` so it never runs during a normal `docker compose up`. Seeding is an explicit opt-in:

```bash
docker compose --profile seed run --rm seed
```

This prevents accidental re-seeding when restarting the stack.

### Seed is idempotent

`seed.py` checks for the existence of Alice's fixed UUID before inserting. If the row exists, it exits early. Fixed UUIDs are intentional — they give you stable IDs to paste into curl commands and tests without having to look anything up.

### Multi-stage Dockerfile

The builder stage installs `gcc` and `libpq-dev` (needed to compile asyncpg). The runtime stage uses `python:3.12-slim` with only `libpq5` (the shared library, ~200 KB vs ~15 MB for the full dev headers). Compiled packages are copied from builder via `COPY --from=builder /root/.local /root/.local`. The result is a minimal image with no build toolchain.

### `selectinload` for cards

`GET /customers/{customer_id}` uses `selectinload(Customer.cards)` rather than a join. This issues two queries (one for the customer, one for cards) instead of a join that would return a row per card. For this access pattern — one customer, a handful of cards — two small queries are cleaner and avoid duplicated customer columns in the result set.

### CORS

`CORSMiddleware` is configured in `main.py` with `allow_origins` set to the frontend origin. In local development this is `http://localhost:5173` (the default Vite dev server port). Update `allow_origins` when deploying to a different domain.

### Card ordering

Cards are returned in `created_at ASC, id ASC` order, enforced at the relationship level in `models.py` via `order_by=[text("cards.created_at"), text("cards.id")]`. The secondary `id` sort is a stable tiebreaker for cards created within the same transaction. Ordering at the model layer means it applies consistently across all query paths without needing an explicit `ORDER BY` in each router.

### `is_archived` soft-delete

Both customers and cards use `is_archived` for soft-deletes. Records are excluded at the query layer (`is_archived.is_(False)`) rather than via a model-level filter or view, keeping the ORM model simple and making it easy to query archived records explicitly via `?include=archived`. Archived records can be restored via `PATCH` with `{ "is_archived": false }`.

## Environment Variables

| Variable       | Default                                                            | Notes                     |
| -------------- | ------------------------------------------------------------------ | ------------------------- |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/coffeecard` | Must use `asyncpg` scheme |

Copy `.env.example` to `.env` for running outside Docker.

## Adding a New Migration

```bash
# With the DB running
docker compose exec api alembic revision --autogenerate -m "describe the change"
```

Alembic will diff `Base.metadata` against the live schema and generate a file in `alembic/versions/`. Review it before committing — autogenerate doesn't detect everything (e.g. check constraints, custom types).

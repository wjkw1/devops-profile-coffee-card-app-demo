# DevOps Profile - Coffee Card Concession App Demo

A functional coffee concession card app designed to demonstrate serverless deployment on AWS. The focus is taking a non-trivial application from local development to production using modern DevOps practices.

AWS services: Lambda + API Gateway + DynamoDB + S3 + CloudFront

## Purpose

An end-to-end showcase of:

- Serverless API on Lambda behind API Gateway, deployed via container image
- NoSQL data modelling with DynamoDB (single-table design)
- Static frontend on S3 + CloudFront
- GitHub Actions CI/CD with OIDC - no static AWS credentials

## Scenario

A salesperson operates a kiosk-style dashboard. They register walk-up customers, sell concession cards with a set number of coffee credits, and redeem coffees by ticking off credits. There is no customer-facing UI because the salesperson controls everything.

## Architecture

See more about this diagram methodology: [C4 Models](https://c4models.com)

### System Context

> ![C4 Context Diagram](diagrams/Coffee%20Cards%20C4%20-%20Context.jpg)

### Container

TODO Update this diagram

> ![C4 Container Diagram](diagrams/Coffee%20Cards%20C4%20-%20Container%20v2.jpg)

## Tech Stack

### API

| Component  | Choice           | Notes                                          |
| ---------- | ---------------- | ---------------------------------------------- |
| Language   | Python 3.12      |                                                |
| Framework  | FastAPI          | Auto-generated OpenAPI docs at `/docs`         |
| Validation | Pydantic v2      | Request/response schemas and settings          |
| Database   | DynamoDB         | Single-table design, boto3                     |
| Runtime    | AWS Lambda       | Mangum ASGI adapter + Lambda Web Adapter       |
| Container  | python:3.12-slim | Multi-stage Dockerfile                         |
| Testing    | pytest + moto    | DynamoDB mocked in-process, no Docker required |
| Linting    | Ruff             | Lint and format in one tool                    |

### Frontend Layer

| Component   | Choice               | Notes                                 |
| ----------- | -------------------- | ------------------------------------- |
| Framework   | React 18             | Single-page app, no SSR needed        |
| Build Tool  | Vite                 | Fast HMR, optimised production builds |
| Styling     | Tailwind CSS v3      | Utility-first, small bundles          |
| HTTP Client | fetch (thin wrapper) | 4–5 endpoints don't justify a library |
| Hosting     | S3 + CloudFront      | Static assets served via CDN          |

### CI/CD (GitHub Actions)

| Concern           | Choice                                                   |
| ----------------- | -------------------------------------------------------- |
| AWS Auth          | OIDC Federation - no static access keys                  |
| API pipeline      | Lint -> Test -> Build -> Push to ECR -> Deploy to Lambda |
| Frontend pipeline | Lint -> Build -> Deploy to S3 -> CloudFront invalidation |
| Coverage          | pytest-cov, reported on every PR                         |

## Getting Started

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/), [Docker Compose](https://docs.docker.com/compose/install/), [pnpm](https://pnpm.io/installation)

| Command     | Does                                                                   |
| ----------- | ---------------------------------------------------------------------- |
| `make dev`  | Starts DynamoDB Local + API in background, runs frontend in foreground |
| `make down` | Stops all Docker services                                              |
| `make seed` | Seeds sample data (Alice + Bob + cards)                                |

The frontend is available at `http://localhost:5173`, the API at `http://localhost:8000`.

Copy `frontend/.env.example` to `frontend/.env.local` and set `VITE_API_BASE_URL=http://localhost:8000` before running `make dev`.

## Data Models

### Customer

| Field       | Type     | Notes                                 |
| ----------- | -------- | ------------------------------------- |
| id          | UUID     | Primary key                           |
| name        | str      | Required                              |
| email       | EmailStr | Optional                              |
| is_archived | bool     | Soft-delete flag, defaults to `false` |
| created_at  | datetime | Set on creation                       |

### Card

| Field         | Type     | Notes                                        |
| ------------- | -------- | -------------------------------------------- |
| id            | UUID     | Primary key                                  |
| customer_id   | UUID     | Reference to Customer                        |
| total_credits | int      | Set on purchase (default 5)                  |
| credits_used  | int      | Incremented on redeem, decremented on refund |
| is_archived   | bool     | Soft-delete flag, defaults to `false`        |
| created_at    | datetime | Set on creation                              |

## API Endpoints

### Customers

| Method | Path                           | Notes                                                      |
| ------ | ------------------------------ | ---------------------------------------------------------- |
| GET    | `/api/customers`               | `?search=` partial name match; `?include=archived` for all |
| POST   | `/api/customers`               | Body: `{ name, email? }`                                   |
| GET    | `/api/customers/{customer_id}` | Returns customer with nested active cards                  |
| PATCH  | `/api/customers/{customer_id}` | Updates `name`, `email`, or `is_archived`                  |
| DELETE | `/api/customers/{customer_id}` | Soft-archives; returns updated customer                    |

### Cards

| Method | Path                                                  | Notes                                          |
| ------ | ----------------------------------------------------- | ---------------------------------------------- |
| GET    | `/api/customers/{customer_id}/cards`                  | `?include=archived` to include archived cards  |
| POST   | `/api/customers/{customer_id}/cards`                  | Creates card with 5 credits                    |
| PATCH  | `/api/customers/{customer_id}/cards/{card_id}`        | Updates `is_archived`                          |
| DELETE | `/api/customers/{customer_id}/cards/{card_id}`        | Soft-delete via `is_archived`                  |
| POST   | `/api/customers/{customer_id}/cards/{card_id}/redeem` | Increments `credits_used`; 409 if at capacity  |
| POST   | `/api/customers/{customer_id}/cards/{card_id}/refund` | Decrements `credits_used`; 409 if already zero |

### Health

| Method | Path          | Notes                                                  |
| ------ | ------------- | ------------------------------------------------------ |
| GET    | `/api/health` | Returns `version`, `uptime_seconds`, `database` status |

## Business Rules

1. A card is created with a configurable number of credits (default 5).
2. Each redemption increments `credits_used` by 1.
3. A redemption on a card with no remaining credits returns 409 Conflict.
4. A refund decrements `credits_used` by 1, down to 0.
5. A refund on a card with 0 credits used returns 409 Conflict.
6. Deleting a customer or card sets `is_archived = true`. Archived records are excluded from listings by default and can be restored via `PATCH`.

## Frontend

A single-page salesperson dashboard providing:

- A search bar to find customers by name
- A register button to create new customers
- A customer view showing active cards and remaining credits
- Redeem and refund buttons on each card

No customer-facing UI, no QR codes, no authentication layer in the MVP.

### Why not a BFF?

A Backend-for-Frontend layer was considered and deliberately skipped. The app has one frontend, no authentication layer, and each view maps to a single API call. The static SPA calling FastAPI directly keeps the architecture simple and the CI/CD pipeline focused on two services rather than three.

## Repository Structure

Two repositories:

1. **devops-profile-coffee-card-app-demo** - Application code (`api/`, `frontend/`)
2. **devops-profile-coffee-card-infra-demo** - Terraform infrastructure (Lambda, API Gateway, DynamoDB, S3/CloudFront)

See [api/README.md](api/README.md) for API implementation details, design decisions, and environment variables.

## Out of Scope for V1

- Customer-facing UI or self-service
- Authentication and authorization
- QR codes or physical card integration
- Per-redemption audit trail
- Fuzzy search
- Card expiry

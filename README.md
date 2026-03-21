# DevOps Profile - Coffee Card Concession App Demo

## Purpose

A functional but simple coffee concession card app designed to showcase DevOps skills and technical depth using a real-world example. The focus is not on building a complex application, it's on deploying an app from development to production using modern practices. The MVP has just enough domain logic to make the API non-trivial (a few endpoints, a database, business logic) without becoming a product build.

## Scenario

A salesperson operates a kiosk-style dashboard. They register walk-up customers, sell concession cards with a set number of coffee credits, and redeem coffees by ticking off credits. There is no customer-facing UI — the salesperson controls everything.

### MVP Features - Salesperson-Controlled Kiosk Model

1. **Customer Registration and Updates**
   The salesperson creates a customer record with a name (and optionally an email or phone). Returns a unique customer ID. This gives you a POST endpoint and a database write.

2. **Purchase a Concession Card**
   Given a customer ID, create a new concession card with a configurable number of "credits" (default 5). Store the purchase timestamp. This is a core domain object and a second POST endpoint.

3. **Redeem a Coffee (Tick a Box)**
   Given a customer ID and card ID, deduct credits from the card. Return remaining credits. This is where the business logic lives, enough to be interesting, and simple enough to not derail the infra work.

4. **View Customer Status**
   GET endpoint returning a customer's active cards and remaining credits. This is your read path and the main thing the frontend displays.

5. **Simple Frontend — Salesperson Dashboard**
   A single-page React + Tailwind app with: a search bar to find a customer by name, a "Register" button, a view of the customer's cards and credits, and a "Redeem" button. No customer-facing UI, no QR codes, no scroll-book aesthetic yet.

6. **Health Check Endpoint**
   A /health route returning app version, uptime, and database connectivity. Small effort, but essential for ECS task health checks and demonstrates operational awareness.

## Data Models

### Customer

| Field       | Type     | Notes                                 |
| ----------- | -------- | ------------------------------------- |
| id          | UUID     | Primary key                           |
| name        | str      | Required                              |
| email       | EmailStr | Optional, lightweight validation      |
| is_archived | bool     | Soft-delete flag, defaults to `false` |
| created_at  | datetime | Set on creation                       |

### Card

| Field             | Type     | Notes                                        |
| ----------------- | -------- | -------------------------------------------- |
| id                | UUID     | Primary key                                  |
| customer_id       | UUID     | FK → Customer                                |
| total_credits     | int      | Set on purchase (default 5)                  |
| remaining_credits | int      | Decremented on redeem, incremented on refund |
| created_at        | datetime | Set on creation                              |

## API Endpoints

### Customers

| Method | Path                     | Description                               |
| ------ | ------------------------ | ----------------------------------------- |
| GET    | /customers               | List customers (supports `?name=` filter) |
| POST   | /customers               | Register a new customer                   |
| GET    | /customers/{customer_id} | View customer status with active cards    |
| PATCH  | /customers/{customer_id} | Update customer details                   |
| DELETE | /customers/{customer_id} | Soft-delete (set archive flag)            |

### Cards

| Method | Path                                     | Description           |
| ------ | ---------------------------------------- | --------------------- |
| GET    | /customers/{customer_id}/cards           | List customer's cards |
| POST   | /customers/{customer_id}/cards           | Purchase a new card   |
| GET    | /customers/{customer_id}/cards/{card_id} | View card detail      |

### Actions

| Method | Path                                            | Description   |
| ------ | ----------------------------------------------- | ------------- |
| POST   | /customers/{customer_id}/cards/{card_id}/redeem | Tick a box    |
| POST   | /customers/{customer_id}/cards/{card_id}/refund | Un-tick a box |

### Health

| Method | Path    | Description                          |
| ------ | ------- | ------------------------------------ |
| GET    | /health | App version, uptime, DB connectivity |

## Business Rules

1. A card is created with a configurable number of credits (default 5).
2. Each redemption deducts 1 credit from the card's `remaining_credits`.
3. A redemption against a card with 0 remaining credits returns a 409 Conflict.
4. A refund adds 1 credit back, up to the card's `total_credits` ceiling.
5. Deleting a customer sets `is_archived = true` rather than removing the row. Archived customers are excluded from `GET /customers` by default.

## Tech Stack

### High Level Architecture Diagrams

See more about this diagram methodology on my [website here](https://westernwilson.com/reflections/c4models), or official docs here: <https://c4models.com>

#### System Context

> ![C4 Context Diagram](diagrams/Coffee%20Cards%20C4%20-%20Context.jpg)

#### Container

> ![C4 Container Diagram](diagrams/Coffee%20Cards%20C4%20-%20Container.jpg)

### API Layer

| Component            | Choice                 | Notes                                                     |
| -------------------- | ---------------------- | --------------------------------------------------------- |
| Language             | Python 3.12            |                                                           |
| Framework            | FastAPI                | Async by default, auto-generated OpenAPI docs             |
| Data Modelling       | Pydantic v2            | Bundled with FastAPI, handles request/response validation |
| ORM                  | SQLAlchemy 2.0 (async) | New 2.0 query style                                       |
| Migrations           | Alembic                | Schema evolution tracked in CI/CD pipeline                |
| Database             | PostgreSQL (AWS RDS)   | Relational integrity for customers, cards, credits        |
| Testing              | pytest + httpx         | Async test client, matches real request patterns          |
| Linting / Formatting | Ruff                   | Replaces flake8, isort, and black in a single tool        |
| Container Base       | python:3.12-slim       | Multi-stage Dockerfile for minimal image size             |

### Frontend Layer

| Component        | Choice                | Notes                                                     |
| ---------------- | --------------------- | --------------------------------------------------------- |
| Framework        | React 18              | No SSR requirement, so no need for Next.js                |
| Build Tool       | Vite                  | Fast HMR, optimised production builds, TypeScript support |
| Styling          | Tailwind CSS v3       | Utility-first, small production bundles with purging      |
| HTTP Client      | fetch (thin wrapper)  | 4-5 endpoints don't justify a library like Axios          |
| State Management | useState / useContext | Single-page kiosk flow doesn't warrant Redux or Zustand   |
| Hosting          | S3 + Cloudfront Site  | Serve assets via CDN                                      |

### CI/CD (GitHub Actions)

| Component      | Choice                                            | Notes                                                      |
| -------------- | ------------------------------------------------- | ---------------------------------------------------------- |
| Platform       | GitHub Actions                                    | Two workflows: API and frontend, directory-scoped triggers |
| AWS Auth       | OIDC Federation                                   | No static access keys                                      |
| Python Linting | Ruff / Black                                      | Single tool for linting and formatting                     |
| JS Linting     | ESLint + Prettier                                 | Standard frontend tooling                                  |
| Test Coverage  | pytest-cov                                        | Coverage reporting in CI                                   |
| Pipeline Steps | Lint → Test → Build → Push to ECR → Deploy to ECS |                                                            |

## Frontend

A single-page salesperson dashboard built with React and Tailwind. The UI provides:

- A search bar to find customers by name
- A register button to create new customers
- A customer view showing active cards and remaining credits
- A redeem button to tick off a credit
- A refund button to reverse a redemption

No customer-facing UI, no QR codes, no authentication layer in the MVP.

There might be room to add Token-based auth (still static SPA) in v2. Where the salesperson logs in, FastAPI issues a JWT, the browser stores it in memory (not localStorage), and sends it with every request. The frontend stays static, the auth logic lives entirely in FastAPI. You'd add a `POST /auth/login` endpoint and a dependency that validates the token on protected routes.

### Why not a BFF?

A Backend-for-Frontend layer was considered and deliberately skipped. BFFs earn their place when multiple clients need tailored response shapes, when server-side auth token management is required, or when a single UI view would otherwise require orchestrating several API calls. None of those apply here. The app has one frontend, no authentication layer, and each view maps cleanly to a single API call. The static SPA served from S3 calling FastAPI directly keeps the architecture simple and the CI/CD pipeline focused on two services rather than three.

## Repository Structure

Three separate repositories:

1. **devops-profile-coffee-card-app-demo** — Application code (api/, frontend/, deploy/)
2. **devops-profile-coffee-card-aws-infra-demo** — Terraform and infrastructure (ECS/EKS)
3. **devops-profile-coffee-card-gitops-demo** — ArgoCD and GitOps configuration

## Out of Scope for V1

- Customer-facing UI or self-service
- Authentication and authorization
- QR codes or physical card integration
- Per-redemption audit trail or coffee type tracking
- Fuzzy search
- Card expiry
- Multiple concurrent modifiers on a single redemption

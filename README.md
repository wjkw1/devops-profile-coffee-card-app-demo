# DevOps Profile - Coffee Card App Demo

## Purpose

This repository is a simple coffee concession card app that has both a frontend and backend api that can be deployed to AWS.

## MVP Features - Salesperson-Controlled Kiosk Model

1. **Customer Registration**
   The salesperson creates a customer record with a name (and optionally an email or phone). Returns a unique customer ID. This gives you a POST endpoint and a database write — foundational for the DevOps story.

2. **Purchase a Concession Card**
   Given a customer ID, create a new concession card with a configurable number of "credits" (default 5). Store the purchase timestamp. This is your core domain object and a second POST endpoint.

3. **Redeem a Coffee (Tick a Box)**
   Given a customer ID and card ID, deduct credits from the card. Accept an optional modifier (e.g. special milk = 1.5x cost instead of 1x). Return remaining credits. This is where your business logic lives — enough to be interesting, simple enough to not derail the infra work.

4. **View Customer Status**
   GET endpoint returning a customer's active cards and remaining credits. This is your read path and the main thing the frontend displays.

5. **Simple Frontend — Salesperson Dashboard**
   A single-page React + Tailwind app with: a search bar to find a customer by name, a "Register" button, a view of the customer's cards and credits, and a "Redeem" button. No customer-facing UI, no QR codes, no scroll-book aesthetic yet.

6. **Health Check Endpoint**
   A /health route returning app version, uptime, and database connectivity. Small effort, but essential for ECS task health checks and demonstrates operational awareness.

## Tech Stack

### High Level C4 Diagrams

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
| Python Linting | Ruff                                              | Single tool for linting and formatting                     |
| JS Linting     | ESLint + Prettier                                 | Standard frontend tooling                                  |
| Test Coverage  | pytest-cov                                        | Coverage reporting in CI                                   |
| Pipeline Steps | Lint → Test → Build → Push to ECR → Deploy to ECS |                                                            |

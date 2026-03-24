from fastapi import FastAPI

from app.routers import customers, health

app = FastAPI(title="Coffee Card API", version="0.1.0")

app.include_router(health.router)
app.include_router(customers.router)


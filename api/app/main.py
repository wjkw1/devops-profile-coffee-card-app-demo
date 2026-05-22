import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middlewares import RequestLoggingMiddleware
from app.routers import cards, customers, health
from app.settings import get_settings

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format=settings.log_format,
)

logger = logging.getLogger(__name__)


app = FastAPI(title="Coffee Card API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(cards.router, prefix="/api")

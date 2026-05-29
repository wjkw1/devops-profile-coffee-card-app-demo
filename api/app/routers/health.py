import time

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException

from app.database import CoffeeCardRepository, get_repository
from app.schemas import HealthResponse
from app.settings import get_settings

settings = get_settings()

router = APIRouter(tags=["health"])

_START_TIME = time.time()
APP_VERSION = settings.app_version


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={
        503: {
            "model": HealthResponse,
            "description": "Database unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "version": "string",
                        "uptime_seconds": 42,
                        "database": "error",
                    }
                }
            },
        }
    },
)
def health(repo: CoffeeCardRepository = Depends(get_repository)):
    health_data = {
        "version": APP_VERSION,
        "uptime_seconds": round(time.time() - _START_TIME),
    }
    try:
        repo.describe_table()
        health_data["database"] = "ok"
        return health_data
    except (BotoCoreError, ClientError) as exc:
        health_data["database"] = "error"
        raise HTTPException(
            status_code=503,
            detail=health_data,
        ) from exc

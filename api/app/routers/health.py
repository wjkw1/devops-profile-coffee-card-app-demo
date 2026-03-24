import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session

router = APIRouter(tags=["health"])

_START_TIME = time.time()
APP_VERSION = "0.1.0"


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)):
    try:
        await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {
        "version": APP_VERSION,
        "uptime_seconds": round(time.time() - _START_TIME),
        "database": db_status,
    }

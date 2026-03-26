import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

# Must be set before app modules are imported (engine is created at module level)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_session
from app.main import app
from app.models import Card, Customer


# --- Factories ---

def make_customer(**kwargs) -> Customer:
    now = datetime.now(timezone.utc)
    customer = Customer(
        name=kwargs.get("name", "Jane Doe"),
        email=kwargs.get("email", "jane@example.com"),
        is_archived=kwargs.get("is_archived", False),
    )
    customer.id = kwargs.get("id", uuid.uuid4())
    customer.created_at = kwargs.get("created_at", now)
    customer.cards = kwargs.get("cards", [])
    return customer


def make_card(customer_id: uuid.UUID = None, **kwargs) -> Card:
    now = datetime.now(timezone.utc)
    card = Card(
        customer_id=customer_id or uuid.uuid4(),
        total_credits=kwargs.get("total_credits", 5),
        credits_used=kwargs.get("credits_used", 0),
        is_archived=kwargs.get("is_archived", False),
    )
    card.id = kwargs.get("id", uuid.uuid4())
    card.created_at = kwargs.get("created_at", now)
    return card


# --- Execute result helpers ---

def scalars_all(rows: list) -> MagicMock:
    """Mock result for session.execute() calls that use .scalars().all()."""
    mock = MagicMock()
    mock.scalars.return_value.all.return_value = rows
    return mock


def scalar_one_or_none(row) -> MagicMock:
    """Mock result for session.execute() calls that use .scalar_one_or_none()."""
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = row
    return mock


# --- Fixtures ---

@pytest.fixture
def mock_session():
    session = AsyncMock()
    # session.add() is synchronous in SQLAlchemy — prevent "coroutine never awaited" warning
    session.add = MagicMock()

    # Simulate DB applying server-side defaults (server_default) on refresh
    async def _refresh(obj):
        if not getattr(obj, "created_at", None):
            obj.created_at = datetime.now(timezone.utc)
        if not getattr(obj, "id", None):
            obj.id = uuid.uuid4()
        if isinstance(obj, Card):
            if getattr(obj, "total_credits", None) is None:
                obj.total_credits = 5
            if getattr(obj, "credits_used", None) is None:
                obj.credits_used = 0
            if getattr(obj, "is_archived", None) is None:
                obj.is_archived = False

    session.refresh.side_effect = _refresh
    return session


@pytest.fixture
async def client(mock_session):
    async def override_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

import os
import uuid
from datetime import datetime, timezone

import boto3
import pytest
from httpx import ASGITransport, AsyncClient
from moto import mock_aws

# Must be set before any app module is imported
# because settings reads APP_ENV at import time.
os.environ.setdefault("APP_ENV", "local")
os.environ.setdefault("TABLE_NAME", "coffee-cards-test")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-southeast-2")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.pop("DYNAMODB_ENDPOINT_URL", None)

from app.database import _get_table
from app.main import app
from app.models import Card, Customer
from app.settings import get_settings

# Flush the settings cache so our env vars above take effect.
get_settings.cache_clear()


# --- Factories ---


def make_customer(**kwargs) -> Customer:
    return Customer(
        id=kwargs.get("id", uuid.uuid4()),
        name=kwargs.get("name", "Jane Doe"),
        email=kwargs.get("email", "jane@example.com"),
        is_archived=kwargs.get("is_archived", False),
        created_at=kwargs.get("created_at", datetime.now(timezone.utc)),
    )


def make_card(customer_id=None, **kwargs) -> Card:
    return Card(
        id=kwargs.get("id", uuid.uuid4()),
        customer_id=customer_id or uuid.uuid4(),
        total_credits=kwargs.get("total_credits", 5),
        credits_used=kwargs.get("credits_used", 0),
        is_archived=kwargs.get("is_archived", False),
        created_at=kwargs.get("created_at", datetime.now(timezone.utc)),
    )


# --- Fixtures ---


@pytest.fixture
def mock_table():
    """Spin up a fresh moto DynamoDB table for each test."""
    with mock_aws():
        _get_table.cache_clear()
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-2")
        table = dynamodb.create_table(
            TableName="coffee-cards-test",
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield table
        _get_table.cache_clear()


@pytest.fixture
async def client(mock_table):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

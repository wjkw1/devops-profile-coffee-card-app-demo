"""Seed the database with sample data for local development."""

import uuid
from typing import Any

import boto3
from botocore.config import Config

from app.models import Card, Customer
from app.settings import get_settings

ALICE_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
BOB_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def seed() -> None:
    settings = get_settings()
    kwargs = {
        "region_name": settings.aws_region,
        "config": Config(retries={"max_attempts": 3, "mode": "standard"}),
    }
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url

    dynamodb: Any = boto3.resource("dynamodb", **kwargs)
    table = dynamodb.Table(settings.table_name)

    existing = table.get_item(
        Key={"PK": f"CUSTOMER#{ALICE_ID}", "SK": f"CUSTOMER#{ALICE_ID}"}
    ).get("Item")
    if existing:
        print("Database already seeded — skipping.")
        return

    for customer in [
        Customer(id=ALICE_ID, name="Alice Johnson", email="alice@example.com"),
        Customer(id=BOB_ID, name="Bob Smith", email=None),
    ]:
        table.put_item(Item=customer.to_item())

    for card in [
        Card(customer_id=ALICE_ID, total_credits=5, credits_used=2),
        Card(customer_id=ALICE_ID, total_credits=5, credits_used=5),
        Card(customer_id=BOB_ID, total_credits=5, credits_used=0),
    ]:
        table.put_item(Item=card.to_item())

    print("Seeding complete.")


if __name__ == "__main__":
    seed()

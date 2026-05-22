from functools import lru_cache
from uuid import UUID

import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config

from app.models import Card, Customer
from app.settings import get_settings

_retry_config = Config(retries={"max_attempts": 10, "mode": "standard"})


@lru_cache
def _get_table():
    settings = get_settings()
    kwargs = {"region_name": settings.aws_region, "config": _retry_config}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url
    dynamodb = boto3.resource("dynamodb", **kwargs)
    return dynamodb.Table(settings.table_name)


class CoffeeCardRepository:
    def __init__(self):
        self._table = _get_table()

    # --- Customers ---

    def list_customers_with_cards(
        self, include_archived: bool = False, search: str | None = None
    ) -> list[tuple[Customer, list[Card]]]:
        # One scan for all items; group by PK in Python to avoid N+1 queries.
        result = self._table.scan()
        by_pk: dict[str, dict] = {}
        for item in result.get("Items", []):
            pk = item["PK"]
            if pk not in by_pk:
                by_pk[pk] = {"customer": None, "cards": []}
            if item["type"] == "customer":
                by_pk[pk]["customer"] = Customer.from_item(item)
            elif item["type"] == "card":
                by_pk[pk]["cards"].append(Card.from_item(item))

        pairs = []
        for data in by_pk.values():
            customer = data["customer"]
            if customer is None:
                continue
            if not include_archived and customer.is_archived:
                continue
            if search and search.lower() not in customer.name.lower():
                continue
            cards = (
                data["cards"]
                if include_archived
                else [c for c in data["cards"] if not c.is_archived]
            )
            pairs.append((customer, cards))

        return pairs

    def get_customer(self, customer_id: UUID) -> Customer | None:
        result = self._table.get_item(
            Key={"PK": f"CUSTOMER#{customer_id}", "SK": f"CUSTOMER#{customer_id}"}
        )
        item = result.get("Item")
        return Customer.from_item(item) if item else None

    def get_customer_with_cards(
        self, customer_id: UUID, include_archived: bool = False
    ) -> tuple[Customer | None, list[Card]]:
        """Single query returns the customer record and all their cards."""
        result = self._table.query(
            KeyConditionExpression=Key("PK").eq(f"CUSTOMER#{customer_id}")
        )
        customer = None
        cards = []
        for item in result.get("Items", []):
            if item["type"] == "customer":
                customer = Customer.from_item(item)
            elif item["type"] == "card":
                card = Card.from_item(item)
                if include_archived or not card.is_archived:
                    cards.append(card)
        return customer, cards

    def put_customer(self, customer: Customer) -> None:
        self._table.put_item(Item=customer.to_item())

    # --- Cards ---

    def get_card(self, customer_id: UUID, card_id: UUID) -> Card | None:
        result = self._table.get_item(
            Key={"PK": f"CUSTOMER#{customer_id}", "SK": f"CARD#{card_id}"}
        )
        item = result.get("Item")
        return Card.from_item(item) if item else None

    def put_card(self, card: Card) -> None:
        self._table.put_item(Item=card.to_item())

    def redeem_credits(self, card: Card) -> Card:
        """Atomically increment credits_used by 1,
        enforcing credits_used < total_credits.

        Raises ClientError with ConditionalCheckFailedException if the card is
        already at capacity (concurrent request beat us to the last credit).
        """
        result = self._table.update_item(
            Key={"PK": card.pk, "SK": card.sk},
            UpdateExpression="SET credits_used = credits_used + :delta",
            ConditionExpression="credits_used < total_credits",
            ExpressionAttributeValues={":delta": 1},
            ReturnValues="ALL_NEW",
        )
        return Card.from_item(result["Attributes"])

    def refund_credits(self, card: Card) -> Card:
        """Atomically decrement credits_used by 1,
        enforcing credits_used > 0.

        Raises ClientError with ConditionalCheckFailedException if credits_used is
        already zero (concurrent refund beat us to the last credit).
        """
        result = self._table.update_item(
            Key={"PK": card.pk, "SK": card.sk},
            UpdateExpression="SET credits_used = credits_used + :delta",
            ConditionExpression="credits_used > :zero",
            ExpressionAttributeValues={":delta": -1, ":zero": 0},
            ReturnValues="ALL_NEW",
        )
        return Card.from_item(result["Attributes"])

    def describe_table(self) -> dict:
        return _get_table().meta.client.describe_table(TableName=_get_table().name)


def get_repository() -> CoffeeCardRepository:
    return CoffeeCardRepository()

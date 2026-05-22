import uuid
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class Customer(BaseModel):
    id: UUID = Field(default_factory=uuid.uuid4)
    name: str
    email: EmailStr | None = None
    is_archived: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def pk(self) -> str:
        return f"CUSTOMER#{self.id}"

    @property
    def sk(self) -> str:
        return f"CUSTOMER#{self.id}"

    def to_item(self) -> dict:
        return {
            "PK": self.pk,
            "SK": self.sk,
            "type": "customer",
            **self.model_dump(mode="json"),
        }

    @classmethod
    def from_item(cls, item: dict) -> "Customer":
        return cls(**{k: v for k, v in item.items() if k not in ("PK", "SK", "type")})


class Card(BaseModel):
    id: UUID = Field(default_factory=uuid.uuid4)
    customer_id: UUID
    total_credits: int = 5
    credits_used: int = 0
    is_archived: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def pk(self) -> str:
        return f"CUSTOMER#{self.customer_id}"

    @property
    def sk(self) -> str:
        return f"CARD#{self.id}"

    def to_item(self) -> dict:
        return {
            "PK": self.pk,
            "SK": self.sk,
            "type": "card",
            **self.model_dump(mode="json"),
        }

    @classmethod
    def from_item(cls, item: dict) -> "Card":
        return cls(**{k: v for k, v in item.items() if k not in ("PK", "SK", "type")})

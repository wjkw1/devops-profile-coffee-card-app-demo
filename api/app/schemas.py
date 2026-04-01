from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

EXAMPLE_CARD_RESPONSE = {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "customer_id": "f1e2d3c4-b5a6-7890-abcd-ef1234567890",
    "total_credits": 5,
    "credits_used": 2,
    "is_archived": False,
    "created_at": "2026-01-15T10:30:00Z",
}


class CustomerCreateRequest(BaseModel):
    """Fields required to register a new customer."""

    name: str
    email: EmailStr | None = None


class CustomerUpdateRequest(BaseModel):
    """Fields that can be updated on an existing customer. All fields are optional."""

    name: str | None = None
    email: EmailStr | None = None
    is_archived: bool | None = None


class CardUpdateRequest(BaseModel):
    """Fields that can be updated on an existing card. All fields are optional."""

    is_archived: bool | None = None


class CardResponse(BaseModel):
    """Represents a single coffee loyalty card belonging to a customer."""

    id: UUID
    customer_id: UUID
    total_credits: int
    credits_used: int
    is_archived: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerResponse(BaseModel):
    """Customer profile including all associated loyalty cards."""

    id: UUID
    name: str
    email: EmailStr | None
    is_archived: bool
    created_at: datetime
    cards: list[CardResponse] = Field(
        default=[],
        examples=[[EXAMPLE_CARD_RESPONSE]],
    )

    model_config = {"from_attributes": True}

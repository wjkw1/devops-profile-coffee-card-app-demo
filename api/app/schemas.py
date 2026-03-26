from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

EXAMPLE_CARD_RESPONSE = {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "customer_id": "f1e2d3c4-b5a6-7890-abcd-ef1234567890",
    "total_credits": 5,
    "remaining_credits": 3,
    "created_at": "2026-01-15T10:30:00Z",
}


class CardResponse(BaseModel):
    """Represents a single coffee loyalty card belonging to a customer."""

    id: UUID
    customer_id: UUID
    total_credits: int
    remaining_credits: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerResponse(BaseModel):
    """Full customer profile including all associated loyalty cards."""

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


class CustomerSummaryResponse(BaseModel):
    """Lightweight customer representation used in list views (excludes cards)."""

    id: UUID
    name: str
    email: EmailStr | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerListResponse(BaseModel):
    """Paginated list of customer summaries."""

    customers: list[CustomerSummaryResponse] = Field(
        default=[],
        examples=[
            [
                {
                    "id": "f1e2d3c4-b5a6-7890-abcd-ef1234567890",
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "created_at": "2026-01-15T10:30:00Z",
                }
            ]
        ],
    )

    model_config = {"from_attributes": True}

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import CoffeeCardRepository, get_repository
from app.models import Card, Customer
from app.schemas import (
    CardResponse,
    CustomerCreateRequest,
    CustomerResponse,
    CustomerUpdateRequest,
)

router = APIRouter(prefix="/customers", tags=["customers"])


def _to_response(
    customer: Customer, cards: list[Card] | None = None
) -> CustomerResponse:
    return CustomerResponse(
        **customer.model_dump(),
        cards=[CardResponse(**c.model_dump()) for c in (cards or [])],
    )


@router.get("", response_model=list[CustomerResponse])
def get_customers(
    include: list[str] = Query(default=[]),
    search: str | None = Query(default=None),
    repo: CoffeeCardRepository = Depends(get_repository),
):
    """Return all customers with their associated active loyalty cards.

    Use `?include=archived` to include archived customers and their archived cards.
    Use `?search=` to filter customers by name (case-insensitive partial match).
    """
    include_archived = "archived" in include
    pairs = repo.list_customers_with_cards(
        include_archived=include_archived, search=search
    )
    return [_to_response(customer, cards) for customer, cards in pairs]


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(
    body: CustomerCreateRequest,
    repo: CoffeeCardRepository = Depends(get_repository),
):
    """Register a new customer."""
    customer = Customer(name=body.name, email=body.email)
    repo.put_customer(customer)
    return _to_response(customer)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: UUID,
    include: list[str] = Query(default=[]),
    repo: CoffeeCardRepository = Depends(get_repository),
):
    """Return a single customer with their associated cards.

    Use `?include=archived` to include archived cards.
    """
    include_archived = "archived" in include
    customer, cards = repo.get_customer_with_cards(
        customer_id, include_archived=include_archived
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return _to_response(customer, cards)


@router.delete("/{customer_id}", response_model=CustomerResponse)
def archive_customer(
    customer_id: UUID,
    repo: CoffeeCardRepository = Depends(get_repository),
):
    """Archive a customer, excluding them from active customer listings."""
    customer = repo.get_customer(customer_id)
    if not customer or customer.is_archived:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer.is_archived = True
    repo.put_customer(customer)
    return _to_response(customer)


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: UUID,
    body: CustomerUpdateRequest,
    repo: CoffeeCardRepository = Depends(get_repository),
):
    """Update one or more fields on an existing customer.

    Set `is_archived: false` to restore an archived customer.
    """
    customer, cards = repo.get_customer_with_cards(customer_id, include_archived=True)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(customer, field, value)
    repo.put_customer(customer)
    return _to_response(customer, cards)

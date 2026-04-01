from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models import Card, Customer
from app.schemas import CustomerResponse, CustomerUpdateRequest

router = APIRouter(prefix="/customers", tags=["customers"])


def _cards_load(include: list[str]):
    """Return a selectinload option for cards, filtered by archive status."""
    if "archived" in include:
        return selectinload(Customer.cards)
    return selectinload(Customer.cards.and_(Card.is_archived.is_(False)))


@router.get("", response_model=list[CustomerResponse])
async def get_customers(
    include: list[str] = Query(default=[]),
    session: AsyncSession = Depends(get_session),
):
    """Return all customers with their associated active loyalty cards.

    Use `?include=archived` to include archived customers and their archived cards.
    """
    query = select(Customer).options(_cards_load(include))

    if "archived" not in include:
        query = query.where(Customer.is_archived.is_(False))

    result = await session.execute(query)
    customers = result.scalars().all()
    if not customers:
        raise HTTPException(status_code=404, detail="Customers not found")
    return customers


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    include: list[str] = Query(default=[]),
    session: AsyncSession = Depends(get_session),
):
    """Return a single customer with their associated active cards.

    Use `?include=archived` to include archived cards.
    """
    result = await session.execute(
        select(Customer).where(Customer.id == customer_id).options(_cards_load(include))
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    body: CustomerUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Update one or more fields on an existing customer.

    Set `is_archived: false` to restore an archived customer.
    """
    result = await session.execute(
        select(Customer)
        .where(Customer.id == customer_id)
        .options(selectinload(Customer.cards))
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(customer, field, value)

    await session.commit()
    await session.refresh(customer)
    return customer

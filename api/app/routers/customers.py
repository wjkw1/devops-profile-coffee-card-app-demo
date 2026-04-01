from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models import Card, Customer
from app.schemas import CustomerCreateRequest, CustomerResponse, CustomerUpdateRequest

router = APIRouter(prefix="/customers", tags=["customers"])


def _cards_load(include: list[str]):
    """Return a selectinload option for cards, filtered by archive status."""
    if "archived" in include:
        return selectinload(Customer.cards)
    return selectinload(Customer.cards.and_(Card.is_archived.is_(False)))


@router.get("", response_model=list[CustomerResponse])
async def get_customers(
    include: list[str] = Query(default=[]),
    search: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    """Return all customers with their associated active loyalty cards.

    Use `?include=archived` to include archived customers and their archived cards.
    Use `?search=` to filter customers by name (case-insensitive partial match).
    """
    query = select(Customer).options(_cards_load(include))

    if "archived" not in include:
        query = query.where(Customer.is_archived.is_(False))

    if search:
        query = query.where(Customer.name.ilike(f"%{search}%"))

    result = await session.execute(query)
    return result.scalars().all()


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(
    body: CustomerCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Register a new customer."""
    customer = Customer(name=body.name, email=body.email)
    session.add(customer)
    await session.commit()
    await session.refresh(customer, attribute_names=["cards"])
    return customer


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


@router.delete("/{customer_id}", response_model=CustomerResponse)
async def archive_customer(
    customer_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Archive a customer, excluding them from active customer listings."""
    customer = await session.get(Customer, customer_id)
    if not customer or customer.is_archived:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer.is_archived = True
    await session.commit()
    await session.refresh(customer, attribute_names=["cards"])
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
    await session.refresh(customer, attribute_names=["cards"])
    return customer

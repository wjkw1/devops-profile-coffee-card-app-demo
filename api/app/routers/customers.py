from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models import Customer
from app.schemas import CustomerListResponse, CustomerResponse

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=CustomerListResponse)
async def get_customers(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Customer).where(Customer.is_archived.is_(False))
    )
    customers = result.scalars().all()
    if not customers:
        raise HTTPException(status_code=404, detail="Customers not found")
    return CustomerListResponse(customers=customers)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Customer)
        .where(Customer.id == customer_id, Customer.is_archived.is_(False))
        .options(selectinload(Customer.cards))
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Card, Customer
from app.schemas import CardResponse, CardUpdateRequest

router = APIRouter(prefix="/customers/{customer_id}/cards", tags=["cards"])


@router.get("", response_model=list[CardResponse])
async def get_cards(
    customer_id: UUID,
    include: list[str] = Query(default=[]),
    session: AsyncSession = Depends(get_session),
):
    """Return all active cards belonging to the given customer.

    Use `?include=archived` to include archived cards as well.
    """
    customer = await session.get(Customer, customer_id)
    if not customer or customer.is_archived:
        raise HTTPException(status_code=404, detail="Customer not found")

    query = select(Card).where(Card.customer_id == customer_id)
    if "archived" not in include:
        query = query.where(Card.is_archived.is_(False))

    result = await session.execute(query)
    return result.scalars().all()


@router.post("", response_model=CardResponse, status_code=201)
async def purchase_card(
    customer_id: UUID, session: AsyncSession = Depends(get_session)
):
    """Purchase a new loyalty card with 5 credits for the given customer."""
    customer = await session.get(Customer, customer_id)
    if not customer or customer.is_archived:
        raise HTTPException(status_code=404, detail="Customer not found")

    card = Card(customer_id=customer_id)
    session.add(card)
    await session.commit()
    await session.refresh(card)
    return card


@router.delete("/{card_id}", status_code=204)
async def archive_card(
    customer_id: UUID, card_id: UUID, session: AsyncSession = Depends(get_session)
):
    """Archive a loyalty card, excluding it from active card listings."""
    customer = await session.get(Customer, customer_id)
    if not customer or customer.is_archived:
        raise HTTPException(status_code=404, detail="Customer not found")

    card = await session.get(Card, card_id)
    if not card or card.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Card not found")

    card.is_archived = True
    await session.commit()


@router.patch("/{card_id}", response_model=CardResponse)
async def update_card(
    customer_id: UUID,
    card_id: UUID,
    body: CardUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Update one or more fields on an existing card.

    Set `is_archived: false` to restore an archived card.
    """
    customer = await session.get(Customer, customer_id)
    if not customer or customer.is_archived:
        raise HTTPException(status_code=404, detail="Customer not found")

    card = await session.get(Card, card_id)
    if not card or card.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Card not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(card, field, value)

    await session.commit()
    await session.refresh(card)
    return card


@router.post("/{card_id}/redeem", status_code=200)
async def redeem_card(
    customer_id: UUID, card_id: UUID, session: AsyncSession = Depends(get_session)
):
    """Redeem a loyalty card, decrementing its credit balance."""
    customer = await session.get(Customer, customer_id)
    if not customer or customer.is_archived:
        raise HTTPException(status_code=404, detail="Customer not found")

    card = await session.get(Card, card_id)
    if not card or card.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Card not found")

    if card.is_archived:
        raise HTTPException(
            status_code=400, detail="Card is archived and cannot be redeemed"
        )
    if card.credits_used >= card.total_credits:
        raise HTTPException(status_code=400, detail="Card has no remaining credits")
    card.credits_used += 1
    await session.commit()
    return card


@router.post("/{card_id}/refund", status_code=200)
async def refund_card(
    customer_id: UUID, card_id: UUID, session: AsyncSession = Depends(get_session)
):
    """Refund a loyalty card, incrementing its credit balance."""

    customer = await session.get(Customer, customer_id)
    if not customer or customer.is_archived:
        raise HTTPException(status_code=404, detail="Customer not found")

    card = await session.get(Card, card_id)
    if not card or card.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Card not found")

    if card.is_archived:
        raise HTTPException(
            status_code=400, detail="Card is archived and cannot be refunded"
        )
    if card.credits_used <= 0:
        raise HTTPException(
            status_code=400, detail="Card has no used credits to refund"
        )
    card.credits_used -= 1
    await session.commit()
    return card

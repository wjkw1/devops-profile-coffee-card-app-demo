from uuid import UUID

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import CoffeeCardRepository, get_repository
from app.models import Card, Customer
from app.schemas import CardResponse, CardUpdateRequest

router = APIRouter(prefix="/customers/{customer_id}/cards", tags=["cards"])


def _get_active_customer(customer_id: UUID, repo: CoffeeCardRepository) -> Customer:
    customer = repo.get_customer(customer_id)
    if not customer or customer.is_archived:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


def _get_card(customer_id: UUID, card_id: UUID, repo: CoffeeCardRepository) -> Card:
    card = repo.get_card(customer_id, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@router.get("", response_model=list[CardResponse])
def get_cards(
    customer_id: UUID,
    include: list[str] = Query(default=[]),
    repo: CoffeeCardRepository = Depends(get_repository),
):
    """Return all active cards belonging to the given customer.

    Use `?include=archived` to include archived cards as well.
    """
    include_archived = "archived" in include
    customer, cards = repo.get_customer_with_cards(
        customer_id, include_archived=include_archived
    )
    if not customer or customer.is_archived:
        raise HTTPException(status_code=404, detail="Customer not found")
    return [CardResponse(**c.model_dump()) for c in cards]


@router.post("", response_model=CardResponse, status_code=201)
def purchase_card(
    customer_id: UUID,
    repo: CoffeeCardRepository = Depends(get_repository),
):
    """Purchase a new loyalty card with 5 credits for the given customer."""
    _get_active_customer(customer_id, repo)
    card = Card(customer_id=customer_id)
    repo.put_card(card)
    return CardResponse(**card.model_dump())


@router.delete("/{card_id}", status_code=204)
def archive_card(
    customer_id: UUID,
    card_id: UUID,
    repo: CoffeeCardRepository = Depends(get_repository),
):
    """Archive a loyalty card, excluding it from active card listings."""
    _get_active_customer(customer_id, repo)
    card = _get_card(customer_id, card_id, repo)
    card.is_archived = True
    repo.put_card(card)


@router.patch("/{card_id}", response_model=CardResponse)
def update_card(
    customer_id: UUID,
    card_id: UUID,
    body: CardUpdateRequest,
    repo: CoffeeCardRepository = Depends(get_repository),
):
    """Update one or more fields on an existing card.

    Set `is_archived: false` to restore an archived card.
    """
    _get_active_customer(customer_id, repo)
    card = _get_card(customer_id, card_id, repo)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(card, field, value)
    repo.put_card(card)
    return CardResponse(**card.model_dump())


@router.post("/{card_id}/redeem", response_model=CardResponse)
def redeem_card(
    customer_id: UUID,
    card_id: UUID,
    repo: CoffeeCardRepository = Depends(get_repository),
):
    """Redeem a loyalty card, decrementing its credit balance."""
    _get_active_customer(customer_id, repo)
    card = _get_card(customer_id, card_id, repo)
    if card.is_archived:
        raise HTTPException(
            status_code=400, detail="Card is archived and cannot be redeemed"
        )
    if card.credits_used >= card.total_credits:
        raise HTTPException(status_code=400, detail="Card has no remaining credits")
    try:
        updated = repo.redeem_credits(card)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=409, detail="Card has no remaining credits")
        raise
    return CardResponse(**updated.model_dump())


@router.post("/{card_id}/refund", response_model=CardResponse)
def refund_card(
    customer_id: UUID,
    card_id: UUID,
    repo: CoffeeCardRepository = Depends(get_repository),
):
    """Refund a loyalty card, incrementing its credit balance."""
    _get_active_customer(customer_id, repo)
    card = _get_card(customer_id, card_id, repo)
    if card.is_archived:
        raise HTTPException(
            status_code=400, detail="Card is archived and cannot be refunded"
        )
    if card.credits_used <= 0:
        raise HTTPException(
            status_code=400, detail="Card has no used credits to refund"
        )
    try:
        updated = repo.refund_credits(card)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=409, detail="Card has no used credits to refund"
            )
        raise
    return CardResponse(**updated.model_dump())

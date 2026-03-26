"""Seed the database with sample data for local development."""

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Card, Customer
from app.settings import get_settings

ALICE_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
BOB_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


async def seed() -> None:
    engine = create_async_engine(get_settings().database_url, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        existing = await session.get(Customer, ALICE_ID)
        if existing:
            print("Database already seeded — skipping.")
            return

        alice = Customer(id=ALICE_ID, name="Alice Johnson", email="alice@example.com")
        bob = Customer(id=BOB_ID, name="Bob Smith", email=None)

        session.add_all([alice, bob])
        await session.flush()

        session.add_all(
            [
                Card(customer_id=ALICE_ID, total_credits=5, credits_used=2),
                Card(customer_id=ALICE_ID, total_credits=5, credits_used=5),
                Card(customer_id=BOB_ID, total_credits=5, credits_used=0),
            ]
        )

        await session.commit()

    await engine.dispose()
    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())

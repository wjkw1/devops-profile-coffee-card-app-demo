import uuid
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from tests.conftest import make_card, make_customer


class TestGetCards:
    async def test_returns_active_cards_for_customer(self, client, mock_table):
        customer = make_customer()
        cards = [make_card(customer_id=customer.id), make_card(customer_id=customer.id)]
        mock_table.put_item(Item=customer.to_item())
        for card in cards:
            mock_table.put_item(Item=card.to_item())

        response = await client.get(f"/api/customers/{customer.id}/cards")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_excludes_archived_cards_by_default(self, client, mock_table):
        customer = make_customer()
        active = make_card(customer_id=customer.id)
        archived = make_card(customer_id=customer.id, is_archived=True)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=active.to_item())
        mock_table.put_item(Item=archived.to_item())

        response = await client.get(f"/api/customers/{customer.id}/cards")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["is_archived"] is False

    async def test_returns_404_for_unknown_customer(self, client, mock_table):
        response = await client.get(f"/api/customers/{uuid.uuid4()}/cards")

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_returns_404_for_archived_customer(self, client, mock_table):
        customer = make_customer(is_archived=True)
        mock_table.put_item(Item=customer.to_item())

        response = await client.get(f"/api/customers/{customer.id}/cards")

        assert response.status_code == 404

    async def test_returns_empty_list_when_no_cards(self, client, mock_table):
        customer = make_customer()
        mock_table.put_item(Item=customer.to_item())

        response = await client.get(f"/api/customers/{customer.id}/cards")

        assert response.status_code == 200
        assert response.json() == []

    async def test_include_archived_returns_all_cards(self, client, mock_table):
        customer = make_customer()
        active = make_card(customer_id=customer.id)
        archived = make_card(customer_id=customer.id, is_archived=True)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=active.to_item())
        mock_table.put_item(Item=archived.to_item())

        response = await client.get(
            f"/api/customers/{customer.id}/cards?include=archived"
        )

        assert response.status_code == 200
        assert len(response.json()) == 2


class TestPurchaseCard:
    async def test_creates_card_for_customer(self, client, mock_table):
        customer = make_customer()
        mock_table.put_item(Item=customer.to_item())

        response = await client.post(f"/api/customers/{customer.id}/cards")

        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == str(customer.id)
        assert data["total_credits"] == 5
        assert data["credits_used"] == 0
        assert data["is_archived"] is False

    async def test_returns_404_for_unknown_customer(self, client, mock_table):
        response = await client.post(f"/api/customers/{uuid.uuid4()}/cards")

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_returns_404_for_archived_customer(self, client, mock_table):
        customer = make_customer(is_archived=True)
        mock_table.put_item(Item=customer.to_item())

        response = await client.post(f"/api/customers/{customer.id}/cards")

        assert response.status_code == 404


class TestArchiveCard:
    async def test_archives_card(self, client, mock_table):
        customer = make_customer()
        card = make_card(customer_id=customer.id)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=card.to_item())

        response = await client.delete(f"/api/customers/{customer.id}/cards/{card.id}")

        assert response.status_code == 204

        # Verify persisted
        item = mock_table.get_item(Key={"PK": card.pk, "SK": card.sk}).get("Item")
        assert item["is_archived"] is True

    async def test_returns_404_for_unknown_customer(self, client, mock_table):
        response = await client.delete(
            f"/api/customers/{uuid.uuid4()}/cards/{uuid.uuid4()}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_returns_404_for_archived_customer(self, client, mock_table):
        customer = make_customer(is_archived=True)
        mock_table.put_item(Item=customer.to_item())

        response = await client.delete(
            f"/api/customers/{customer.id}/cards/{uuid.uuid4()}"
        )

        assert response.status_code == 404

    async def test_returns_404_when_card_not_found(self, client, mock_table):
        customer = make_customer()
        mock_table.put_item(Item=customer.to_item())

        response = await client.delete(
            f"/api/customers/{customer.id}/cards/{uuid.uuid4()}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Card not found"

    async def test_returns_404_when_card_belongs_to_different_customer(
        self, client, mock_table
    ):
        customer = make_customer()
        other_customer = make_customer()
        card = make_card(customer_id=other_customer.id)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=other_customer.to_item())
        mock_table.put_item(Item=card.to_item())

        # Card PK is scoped to other_customer — lookup under customer returns 404.
        response = await client.delete(f"/api/customers/{customer.id}/cards/{card.id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Card not found"


class TestUpdateCard:
    async def test_restores_archived_card(self, client, mock_table):
        customer = make_customer()
        card = make_card(customer_id=customer.id, is_archived=True)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=card.to_item())

        response = await client.patch(
            f"/api/customers/{customer.id}/cards/{card.id}",
            json={"is_archived": False},
        )

        assert response.status_code == 200
        assert response.json()["is_archived"] is False

    async def test_archives_card_via_patch(self, client, mock_table):
        customer = make_customer()
        card = make_card(customer_id=customer.id)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=card.to_item())

        response = await client.patch(
            f"/api/customers/{customer.id}/cards/{card.id}",
            json={"is_archived": True},
        )

        assert response.status_code == 200
        assert response.json()["is_archived"] is True

    async def test_returns_404_for_unknown_customer(self, client, mock_table):
        response = await client.patch(
            f"/api/customers/{uuid.uuid4()}/cards/{uuid.uuid4()}",
            json={"is_archived": False},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_returns_404_for_unknown_card(self, client, mock_table):
        customer = make_customer()
        mock_table.put_item(Item=customer.to_item())

        response = await client.patch(
            f"/api/customers/{customer.id}/cards/{uuid.uuid4()}",
            json={"is_archived": False},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Card not found"


class TestRedeemCard:
    async def test_redeem_card_success(self, client, mock_table):
        customer = make_customer()
        card = make_card(customer_id=customer.id, total_credits=5, credits_used=0)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=card.to_item())

        response = await client.post(
            f"/api/customers/{customer.id}/cards/{card.id}/redeem"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["credits_used"] == 1
        assert data["total_credits"] == 5

    async def test_redeem_card_errors_when_no_remaining_credits(
        self, client, mock_table
    ):
        customer = make_customer()
        card = make_card(customer_id=customer.id, total_credits=5, credits_used=5)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=card.to_item())

        response = await client.post(
            f"/api/customers/{customer.id}/cards/{card.id}/redeem"
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Card has no remaining credits"

    async def test_redeem_archived_card_errors(self, client, mock_table):
        customer = make_customer()
        card = make_card(customer_id=customer.id, credits_used=0, is_archived=True)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=card.to_item())

        response = await client.post(
            f"/api/customers/{customer.id}/cards/{card.id}/redeem"
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Card is archived and cannot be redeemed"

    async def test_redeem_returns_404_for_unknown_customer(self, client, mock_table):
        response = await client.post(
            f"/api/customers/{uuid.uuid4()}/cards/{uuid.uuid4()}/redeem"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_redeem_returns_404_for_unknown_card(self, client, mock_table):
        customer = make_customer()
        mock_table.put_item(Item=customer.to_item())

        response = await client.post(
            f"/api/customers/{customer.id}/cards/{uuid.uuid4()}/redeem"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Card not found"

    async def test_redeem_returns_409_on_concurrent_exhaustion(
        self, client, mock_table
    ):
        """Concurrent request exhausted credits between our pre-check and the write."""
        from app.database import get_repository
        from app.main import app

        customer = make_customer()
        card = make_card(customer_id=customer.id, total_credits=5, credits_used=4)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=card.to_item())

        def broken_repo():
            repo = MagicMock()
            repo.get_customer.return_value = customer
            repo.get_card.return_value = card
            repo.redeem_credits.side_effect = ClientError(
                {
                    "Error": {
                        "Code": "ConditionalCheckFailedException",
                        "Message": "The conditional request failed",
                    }
                },
                "UpdateItem",
            )
            return repo

        app.dependency_overrides[get_repository] = broken_repo
        try:
            response = await client.post(
                f"/api/customers/{customer.id}/cards/{card.id}/redeem"
            )
            assert response.status_code == 409
            assert response.json()["detail"] == "Card has no remaining credits"
        finally:
            app.dependency_overrides.clear()


class TestRefundCard:
    async def test_refund_card_success(self, client, mock_table):
        customer = make_customer()
        card = make_card(customer_id=customer.id, total_credits=5, credits_used=5)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=card.to_item())

        response = await client.post(
            f"/api/customers/{customer.id}/cards/{card.id}/refund"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["credits_used"] == 4
        assert data["total_credits"] == 5

    async def test_refund_card_errors_when_no_used_credits(self, client, mock_table):
        customer = make_customer()
        card = make_card(customer_id=customer.id, total_credits=5, credits_used=0)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=card.to_item())

        response = await client.post(
            f"/api/customers/{customer.id}/cards/{card.id}/refund"
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Card has no used credits to refund"

    async def test_refund_archived_card_errors(self, client, mock_table):
        customer = make_customer()
        card = make_card(customer_id=customer.id, credits_used=3, is_archived=True)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=card.to_item())

        response = await client.post(
            f"/api/customers/{customer.id}/cards/{card.id}/refund"
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Card is archived and cannot be refunded"

    async def test_refund_returns_404_for_unknown_customer(self, client, mock_table):
        response = await client.post(
            f"/api/customers/{uuid.uuid4()}/cards/{uuid.uuid4()}/refund"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_refund_returns_404_for_unknown_card(self, client, mock_table):
        customer = make_customer()
        mock_table.put_item(Item=customer.to_item())

        response = await client.post(
            f"/api/customers/{customer.id}/cards/{uuid.uuid4()}/refund"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Card not found"

    async def test_refund_returns_409_on_concurrent_zero(self, client, mock_table):
        """Concurrent refund drained credits_used to 0 between pre-check and write."""
        from app.database import get_repository
        from app.main import app

        customer = make_customer()
        card = make_card(customer_id=customer.id, total_credits=5, credits_used=1)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=card.to_item())

        def broken_repo():
            repo = MagicMock()
            repo.get_customer.return_value = customer
            repo.get_card.return_value = card
            repo.refund_credits.side_effect = ClientError(
                {
                    "Error": {
                        "Code": "ConditionalCheckFailedException",
                        "Message": "The conditional request failed",
                    }
                },
                "UpdateItem",
            )
            return repo

        app.dependency_overrides[get_repository] = broken_repo
        try:
            response = await client.post(
                f"/api/customers/{customer.id}/cards/{card.id}/refund"
            )
            assert response.status_code == 409
            assert response.json()["detail"] == "Card has no used credits to refund"
        finally:
            app.dependency_overrides.clear()

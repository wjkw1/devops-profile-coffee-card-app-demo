import uuid

from tests.conftest import make_card, make_customer, scalars_all


class TestGetCards:
    async def test_returns_active_cards_for_customer(self, client, mock_session):
        customer = make_customer()
        cards = [make_card(customer_id=customer.id), make_card(customer_id=customer.id)]
        mock_session.get.return_value = customer
        mock_session.execute.return_value = scalars_all(cards)

        response = await client.get(f"/api/customers/{customer.id}/cards")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_returns_404_for_unknown_customer(self, client, mock_session):
        mock_session.get.return_value = None

        response = await client.get(f"/api/customers/{uuid.uuid4()}/cards")

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_returns_404_for_archived_customer(self, client, mock_session):
        mock_session.get.return_value = make_customer(is_archived=True)

        response = await client.get(f"/api/customers/{uuid.uuid4()}/cards")

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_returns_empty_list_when_no_cards(self, client, mock_session):
        customer = make_customer()
        mock_session.get.return_value = customer
        mock_session.execute.return_value = scalars_all([])

        response = await client.get(f"/api/customers/{customer.id}/cards")

        assert response.status_code == 200
        assert response.json() == []

    async def test_include_archived_returns_all_cards(self, client, mock_session):
        customer = make_customer()
        active = make_card(customer_id=customer.id)
        archived = make_card(customer_id=customer.id, is_archived=True)
        mock_session.get.return_value = customer
        mock_session.execute.return_value = scalars_all([active, archived])

        response = await client.get(
            f"/api/customers/{customer.id}/cards?include=archived"
        )

        assert response.status_code == 200
        assert len(response.json()) == 2


class TestPurchaseCard:
    async def test_creates_card_for_customer(self, client, mock_session):
        customer = make_customer()
        mock_session.get.return_value = customer

        response = await client.post(f"/api/customers/{customer.id}/cards")

        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == str(customer.id)
        assert data["total_credits"] == 5
        assert data["credits_used"] == 0
        assert data["is_archived"] is False
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_returns_404_for_unknown_customer(self, client, mock_session):
        mock_session.get.return_value = None

        response = await client.post(f"/api/customers/{uuid.uuid4()}/cards")

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_returns_404_for_archived_customer(self, client, mock_session):
        mock_session.get.return_value = make_customer(is_archived=True)

        response = await client.post(f"/api/customers/{uuid.uuid4()}/cards")

        assert response.status_code == 404


class TestArchiveCard:
    async def test_archives_card(self, client, mock_session):
        customer = make_customer()
        card = make_card(customer_id=customer.id)
        mock_session.get.side_effect = [customer, card]

        response = await client.delete(f"/api/customers/{customer.id}/cards/{card.id}")

        assert response.status_code == 204
        assert card.is_archived is True
        mock_session.commit.assert_called_once()

    async def test_returns_404_for_unknown_customer(self, client, mock_session):
        mock_session.get.return_value = None

        response = await client.delete(
            f"/api/customers/{uuid.uuid4()}/cards/{uuid.uuid4()}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_returns_404_for_archived_customer(self, client, mock_session):
        mock_session.get.return_value = make_customer(is_archived=True)

        response = await client.delete(
            f"/api/customers/{uuid.uuid4()}/cards/{uuid.uuid4()}"
        )

        assert response.status_code == 404

    async def test_returns_404_when_card_not_found(self, client, mock_session):
        customer = make_customer()
        mock_session.get.side_effect = [customer, None]

        response = await client.delete(
            f"/api/customers/{customer.id}/cards/{uuid.uuid4()}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Card not found"

    async def test_returns_404_when_card_belongs_to_different_customer(
        self, client, mock_session
    ):
        customer = make_customer()
        other_customer_id = uuid.uuid4()
        card = make_card(customer_id=other_customer_id)
        mock_session.get.side_effect = [customer, card]

        response = await client.delete(f"/api/customers/{customer.id}/cards/{card.id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Card not found"


class TestUpdateCard:
    async def test_restores_archived_card(self, client, mock_session):
        customer = make_customer()
        card = make_card(customer_id=customer.id, is_archived=True)
        mock_session.get.side_effect = [customer, card]

        response = await client.patch(
            f"/api/customers/{customer.id}/cards/{card.id}",
            json={"is_archived": False},
        )

        assert response.status_code == 200
        assert response.json()["is_archived"] is False
        mock_session.commit.assert_called_once()

    async def test_archives_card_via_patch(self, client, mock_session):
        customer = make_customer()
        card = make_card(customer_id=customer.id, is_archived=False)
        mock_session.get.side_effect = [customer, card]

        response = await client.patch(
            f"/api/customers/{customer.id}/cards/{card.id}",
            json={"is_archived": True},
        )

        assert response.status_code == 200
        assert response.json()["is_archived"] is True

    async def test_returns_404_for_unknown_customer(self, client, mock_session):
        mock_session.get.return_value = None

        response = await client.patch(
            f"/api/customers/{uuid.uuid4()}/cards/{uuid.uuid4()}",
            json={"is_archived": False},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_returns_404_for_unknown_card(self, client, mock_session):
        customer = make_customer()
        mock_session.get.side_effect = [customer, None]

        response = await client.patch(
            f"/api/customers/{customer.id}/cards/{uuid.uuid4()}",
            json={"is_archived": False},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Card not found"

    async def test_returns_404_when_card_belongs_to_different_customer(
        self, client, mock_session
    ):
        customer = make_customer()
        card = make_card(customer_id=uuid.uuid4())
        mock_session.get.side_effect = [customer, card]

        response = await client.patch(
            f"/api/customers/{customer.id}/cards/{card.id}",
            json={"is_archived": False},
        )

        assert response.status_code == 404


class TestRedeemCard:
    """Tests for redeeming credits on a card. These operations are only
    valid on active cards, and should return 400 if attempting to redeem with no
    remaining credits or refund with no used credits."""

    async def test_redeem_card_success(self, client, mock_session):
        customer = make_customer()
        card = make_card(
            customer_id=customer.id, total_credits=5, credits_used=0, is_archived=False
        )
        mock_session.get.side_effect = [customer, card]
        response = await client.post(
            f"/api/customers/{customer.id}/cards/{card.id}/redeem"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_credits"] == 5
        assert data["credits_used"] == 1
        assert data["is_archived"] is False
        mock_session.commit.assert_called_once()

    async def test_redeem_card_errors(self, client, mock_session):
        customer = make_customer()
        card = make_card(
            customer_id=customer.id, total_credits=5, credits_used=5, is_archived=False
        )
        mock_session.get.side_effect = [customer, card]
        response = await client.post(
            f"/api/customers/{customer.id}/cards/{card.id}/redeem"
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Card has no remaining credits"
        mock_session.commit.assert_not_called()

    async def test_redeem_archived_card_errors(self, client, mock_session):
        customer = make_customer()
        card = make_card(
            customer_id=customer.id, total_credits=5, credits_used=0, is_archived=True
        )
        mock_session.get.side_effect = [customer, card]
        response = await client.post(
            f"/api/customers/{customer.id}/cards/{card.id}/redeem"
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Card is archived and cannot be redeemed"
        mock_session.commit.assert_not_called()

    async def test_redeem_returns_404_for_unknown_customer(self, client, mock_session):
        mock_session.get.return_value = None

        response = await client.post(
            f"/api/customers/{uuid.uuid4()}/cards/{uuid.uuid4()}/redeem"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_redeem_returns_404_for_unknown_card(self, client, mock_session):
        customer = make_customer()
        mock_session.get.side_effect = [customer, None]

        response = await client.post(
            f"/api/customers/{customer.id}/cards/{uuid.uuid4()}/redeem"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Card not found"


class TestRefundCard:
    """Tests for refunding credits on a card. These operations are only
    valid on active cards, and should return 400 if attempting to refund with no
    used credits."""

    async def test_refund_card_success(self, client, mock_session):
        customer = make_customer()
        card = make_card(
            customer_id=customer.id, total_credits=5, credits_used=5, is_archived=False
        )
        mock_session.get.side_effect = [customer, card]
        response = await client.post(
            f"/api/customers/{customer.id}/cards/{card.id}/refund"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_credits"] == 5
        assert data["credits_used"] == 4
        assert data["is_archived"] is False
        mock_session.commit.assert_called_once()

    async def test_refund_card_errors(self, client, mock_session):
        customer = make_customer()
        card = make_card(
            customer_id=customer.id, total_credits=5, credits_used=0, is_archived=False
        )
        mock_session.get.side_effect = [customer, card]
        response = await client.post(
            f"/api/customers/{customer.id}/cards/{card.id}/refund"
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Card has no used credits to refund"
        mock_session.commit.assert_not_called()

    async def test_refund_card_archived_errors(self, client, mock_session):
        customer = make_customer()
        card = make_card(
            customer_id=customer.id, total_credits=5, credits_used=5, is_archived=True
        )
        mock_session.get.side_effect = [customer, card]
        response = await client.post(
            f"/api/customers/{customer.id}/cards/{card.id}/refund"
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Card is archived and cannot be refunded"
        mock_session.commit.assert_not_called()

    async def test_refund_returns_404_for_unknown_customer(self, client, mock_session):
        mock_session.get.return_value = None

        response = await client.post(
            f"/api/customers/{uuid.uuid4()}/cards/{uuid.uuid4()}/refund"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_refund_returns_404_for_unknown_card(self, client, mock_session):
        customer = make_customer()
        mock_session.get.side_effect = [customer, None]

        response = await client.post(
            f"/api/customers/{customer.id}/cards/{uuid.uuid4()}/refund"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Card not found"

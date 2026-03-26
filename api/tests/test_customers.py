import uuid

import pytest

from tests.conftest import make_card, make_customer, scalar_one_or_none, scalars_all


class TestListCustomers:
    async def test_returns_active_customers(self, client, mock_session):
        customers = [make_customer(), make_customer(name="Bob")]
        mock_session.execute.return_value = scalars_all(customers)

        response = await client.get("/customers")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Jane Doe"
        assert data[1]["name"] == "Bob"

    async def test_returns_404_when_no_customers(self, client, mock_session):
        mock_session.execute.return_value = scalars_all([])

        response = await client.get("/customers")

        assert response.status_code == 404
        assert response.json()["detail"] == "Customers not found"

    async def test_includes_cards_on_each_customer(self, client, mock_session):
        customer = make_customer()
        customer.cards = [make_card(customer_id=customer.id)]
        mock_session.execute.return_value = scalars_all([customer])

        response = await client.get("/customers")

        assert response.status_code == 200
        assert len(response.json()[0]["cards"]) == 1

    async def test_include_archived_passes_through(self, client, mock_session):
        archived = make_customer(is_archived=True)
        mock_session.execute.return_value = scalars_all([archived])

        response = await client.get("/customers?include=archived")

        assert response.status_code == 200
        assert response.json()[0]["is_archived"] is True


class TestGetCustomer:
    async def test_returns_customer_by_id(self, client, mock_session):
        customer = make_customer()
        mock_session.execute.return_value = scalar_one_or_none(customer)

        response = await client.get(f"/customers/{customer.id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(customer.id)
        assert response.json()["name"] == customer.name

    async def test_returns_404_for_unknown_id(self, client, mock_session):
        mock_session.execute.return_value = scalar_one_or_none(None)

        response = await client.get(f"/customers/{uuid.uuid4()}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_returns_customer_with_active_cards(self, client, mock_session):
        customer = make_customer()
        customer.cards = [make_card(customer_id=customer.id, credits_used=2)]
        mock_session.execute.return_value = scalar_one_or_none(customer)

        response = await client.get(f"/customers/{customer.id}")

        assert response.status_code == 200
        assert response.json()["cards"][0]["credits_used"] == 2

    async def test_invalid_uuid_returns_422(self, client, mock_session):
        response = await client.get("/customers/not-a-uuid")

        assert response.status_code == 422


class TestUpdateCustomer:
    async def test_updates_name(self, client, mock_session):
        customer = make_customer(name="Old Name")
        mock_session.execute.return_value = scalar_one_or_none(customer)

        response = await client.patch(
            f"/customers/{customer.id}", json={"name": "New Name"}
        )

        assert response.status_code == 200
        assert response.json()["name"] == "New Name"
        mock_session.commit.assert_called_once()

    async def test_updates_email(self, client, mock_session):
        customer = make_customer(email="old@example.com")
        mock_session.execute.return_value = scalar_one_or_none(customer)

        response = await client.patch(
            f"/customers/{customer.id}", json={"email": "new@example.com"}
        )

        assert response.status_code == 200
        assert response.json()["email"] == "new@example.com"

    async def test_archives_customer(self, client, mock_session):
        customer = make_customer(is_archived=False)
        mock_session.execute.return_value = scalar_one_or_none(customer)

        response = await client.patch(
            f"/customers/{customer.id}", json={"is_archived": True}
        )

        assert response.status_code == 200
        assert response.json()["is_archived"] is True

    async def test_restores_archived_customer(self, client, mock_session):
        customer = make_customer(is_archived=True)
        mock_session.execute.return_value = scalar_one_or_none(customer)

        response = await client.patch(
            f"/customers/{customer.id}", json={"is_archived": False}
        )

        assert response.status_code == 200
        assert response.json()["is_archived"] is False

    async def test_returns_404_for_unknown_id(self, client, mock_session):
        mock_session.execute.return_value = scalar_one_or_none(None)

        response = await client.patch(
            f"/customers/{uuid.uuid4()}", json={"name": "Ghost"}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_partial_update_ignores_none_fields(self, client, mock_session):
        customer = make_customer(name="Unchanged", email="keep@example.com")
        mock_session.execute.return_value = scalar_one_or_none(customer)

        response = await client.patch(
            f"/customers/{customer.id}", json={"name": "Changed"}
        )

        assert response.status_code == 200
        assert response.json()["email"] == "keep@example.com"

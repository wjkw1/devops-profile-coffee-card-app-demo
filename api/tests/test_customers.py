import uuid

from tests.conftest import make_card, make_customer


class TestListCustomers:
    async def test_returns_active_customers(self, client, mock_table):
        c1 = make_customer(name="Jane Doe")
        c2 = make_customer(name="Bob")
        mock_table.put_item(Item=c1.to_item())
        mock_table.put_item(Item=c2.to_item())

        response = await client.get("/api/customers")

        assert response.status_code == 200
        names = {c["name"] for c in response.json()}
        assert names == {"Jane Doe", "Bob"}

    async def test_returns_empty_list_when_no_customers(self, client, mock_table):
        response = await client.get("/api/customers")

        assert response.status_code == 200
        assert response.json() == []

    async def test_excludes_archived_customers_by_default(self, client, mock_table):
        active = make_customer(name="Active")
        archived = make_customer(name="Archived", is_archived=True)
        mock_table.put_item(Item=active.to_item())
        mock_table.put_item(Item=archived.to_item())

        response = await client.get("/api/customers")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Active"

    async def test_includes_cards_on_each_customer(self, client, mock_table):
        customer = make_customer()
        card = make_card(customer_id=customer.id)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=card.to_item())

        response = await client.get("/api/customers")

        assert response.status_code == 200
        assert len(response.json()[0]["cards"]) == 1

    async def test_include_archived_returns_archived_customers(
        self, client, mock_table
    ):
        archived = make_customer(is_archived=True)
        mock_table.put_item(Item=archived.to_item())

        response = await client.get("/api/customers?include=archived")

        assert response.status_code == 200
        assert response.json()[0]["is_archived"] is True

    async def test_search_filters_by_name(self, client, mock_table):
        alice = make_customer(name="Alice")
        bob = make_customer(name="Bob")
        mock_table.put_item(Item=alice.to_item())
        mock_table.put_item(Item=bob.to_item())

        response = await client.get("/api/customers?search=ali")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Alice"


class TestCreateCustomer:
    async def test_creates_customer(self, client, mock_table):
        response = await client.post(
            "/api/customers",
            json={"name": "New Customer", "email": "new@example.com"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Customer"
        assert data["email"] == "new@example.com"
        assert data["is_archived"] is False
        assert data["cards"] == []

    async def test_creates_customer_without_email(self, client, mock_table):
        response = await client.post("/api/customers", json={"name": "No Email"})

        assert response.status_code == 201
        assert response.json()["email"] is None

    async def test_returns_422_when_name_missing(self, client, mock_table):
        response = await client.post("/api/customers", json={"email": "x@example.com"})

        assert response.status_code == 422


class TestGetCustomer:
    async def test_returns_customer_by_id(self, client, mock_table):
        customer = make_customer()
        mock_table.put_item(Item=customer.to_item())

        response = await client.get(f"/api/customers/{customer.id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(customer.id)
        assert response.json()["name"] == customer.name

    async def test_returns_404_for_unknown_id(self, client, mock_table):
        response = await client.get(f"/api/customers/{uuid.uuid4()}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_returns_customer_with_active_cards(self, client, mock_table):
        customer = make_customer()
        card = make_card(customer_id=customer.id, credits_used=2)
        mock_table.put_item(Item=customer.to_item())
        mock_table.put_item(Item=card.to_item())

        response = await client.get(f"/api/customers/{customer.id}")

        assert response.status_code == 200
        assert response.json()["cards"][0]["credits_used"] == 2

    async def test_invalid_uuid_returns_422(self, client, mock_table):
        response = await client.get("/api/customers/not-a-uuid")

        assert response.status_code == 422


class TestUpdateCustomer:
    async def test_updates_name(self, client, mock_table):
        customer = make_customer(name="Old Name")
        mock_table.put_item(Item=customer.to_item())

        response = await client.patch(
            f"/api/customers/{customer.id}", json={"name": "New Name"}
        )

        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    async def test_updates_email(self, client, mock_table):
        customer = make_customer(email="old@example.com")
        mock_table.put_item(Item=customer.to_item())

        response = await client.patch(
            f"/api/customers/{customer.id}", json={"email": "new@example.com"}
        )

        assert response.status_code == 200
        assert response.json()["email"] == "new@example.com"

    async def test_archives_customer(self, client, mock_table):
        customer = make_customer(is_archived=False)
        mock_table.put_item(Item=customer.to_item())

        response = await client.patch(
            f"/api/customers/{customer.id}", json={"is_archived": True}
        )

        assert response.status_code == 200
        assert response.json()["is_archived"] is True

    async def test_restores_archived_customer(self, client, mock_table):
        customer = make_customer(is_archived=True)
        mock_table.put_item(Item=customer.to_item())

        response = await client.patch(
            f"/api/customers/{customer.id}", json={"is_archived": False}
        )

        assert response.status_code == 200
        assert response.json()["is_archived"] is False

    async def test_returns_404_for_unknown_id(self, client, mock_table):
        response = await client.patch(
            f"/api/customers/{uuid.uuid4()}", json={"name": "Ghost"}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_partial_update_ignores_none_fields(self, client, mock_table):
        customer = make_customer(name="Unchanged", email="keep@example.com")
        mock_table.put_item(Item=customer.to_item())

        response = await client.patch(
            f"/api/customers/{customer.id}", json={"name": "Changed"}
        )

        assert response.status_code == 200
        assert response.json()["email"] == "keep@example.com"


class TestArchiveCustomer:
    async def test_archives_active_customer(self, client, mock_table):
        customer = make_customer(is_archived=False)
        mock_table.put_item(Item=customer.to_item())

        response = await client.delete(f"/api/customers/{customer.id}")

        assert response.status_code == 200
        assert response.json()["is_archived"] is True

    async def test_returns_404_for_unknown_customer(self, client, mock_table):
        response = await client.delete(f"/api/customers/{uuid.uuid4()}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    async def test_returns_404_for_already_archived_customer(self, client, mock_table):
        customer = make_customer(is_archived=True)
        mock_table.put_item(Item=customer.to_item())

        response = await client.delete(f"/api/customers/{customer.id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

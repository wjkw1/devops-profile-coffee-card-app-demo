from unittest.mock import MagicMock

from botocore.exceptions import ClientError


class TestHealth:
    async def test_returns_ok_when_db_is_healthy(self, client, mock_table):
        response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["database"] == "ok"
        assert data["version"] == "0.1.0"
        assert isinstance(data["uptime_seconds"], int)

    async def test_returns_error_when_db_is_unavailable(self, client, mock_table):
        from app.database import get_repository
        from app.main import app

        def broken_repo():
            repo = MagicMock()
            repo.describe_table.side_effect = ClientError(
                {
                    "Error": {
                        "Code": "ResourceNotFoundException",
                        "Message": "Table not found",
                    }
                },
                "DescribeTable",
            )
            return repo

        app.dependency_overrides[get_repository] = broken_repo
        try:
            response = await client.get("/api/health")
            assert response.status_code == 503
            response_json_details = response.json().get("detail", {})

            assert response_json_details["version"] == "0.1.0"
            assert isinstance(response_json_details["uptime_seconds"], int)
            assert response_json_details["database"] == "error"
        finally:
            app.dependency_overrides.clear()

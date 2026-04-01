from unittest.mock import AsyncMock


class TestHealth:
    async def test_returns_ok_when_db_is_healthy(self, client, mock_session):
        response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["database"] == "ok"
        assert data["version"] == "0.1.0"
        assert isinstance(data["uptime_seconds"], int)

    async def test_returns_error_when_db_is_unavailable(self, client, mock_session):
        mock_session.execute = AsyncMock(side_effect=Exception("connection refused"))

        response = await client.get("/api/health")

        assert response.status_code == 200
        assert response.json()["database"] == "error"

import logging


class TestRequestLoggingMiddleware:
    async def test_logs_required_fields(self, client, caplog):
        with caplog.at_level(logging.INFO, logger="app.middlewares"):
            response = await client.get("/api/health")

        assert response.status_code == 200
        records = [r for r in caplog.records if r.name == "app.middlewares"]
        assert len(records) == 1
        record = records[0]

        assert record.method == "GET"
        assert record.path == "/api/health"
        assert record.status == 200
        assert isinstance(record.duration_ms, float)
        assert record.correlation_id

    async def test_uses_trace_id_header_as_correlation_id(self, client, caplog):
        trace_id = "Root=1-abc-123"
        with caplog.at_level(logging.INFO, logger="app.middlewares"):
            response = await client.get(
                "/api/health", headers={"X-Amzn-Trace-Id": trace_id}
            )

        assert response.status_code == 200
        record = next(r for r in caplog.records if r.name == "app.middlewares")
        assert record.correlation_id == trace_id

    async def test_echoes_correlation_id_in_response_header(self, client, caplog):
        with caplog.at_level(logging.INFO, logger="app.middlewares"):
            response = await client.get("/api/health")

        record = next(r for r in caplog.records if r.name == "app.middlewares")
        assert response.headers["X-Request-Id"] == record.correlation_id

import asyncio
import os

import httpx
import pytest

from f1_api.main import create_app


@pytest.mark.integration
def test_health_endpoint_over_http() -> None:
    if os.getenv("RUN_HTTP_INTEGRATION") != "1":
        pytest.skip("Set RUN_HTTP_INTEGRATION=1 to run HTTP-style integration tests.")

    async def _run() -> None:
        transport = httpx.ASGITransport(app=create_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    asyncio.run(_run())

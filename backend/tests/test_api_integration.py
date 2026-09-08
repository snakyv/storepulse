import httpx
import pytest

from app.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_store_api_lists_seeded_stores_and_accepts_heartbeat() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        stores_response = await client.get("/api/v1/stores")
        heartbeat_response = await client.post("/api/v1/stores/MAD-MADRID/heartbeat")

    assert stores_response.status_code == 200
    stores = stores_response.json()
    assert len(stores) == 5
    assert {store["code"] for store in stores} == {
        "MAD-LONDON",
        "MAD-MADRID",
        "MAD-NYC",
        "MAD-TOKYO",
        "MAD-WARSAW",
    }
    assert heartbeat_response.status_code == 200
    assert heartbeat_response.json()["store_code"] == "MAD-MADRID"
    assert heartbeat_response.json()["status"] == "accepted"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unknown_store_heartbeat_returns_404() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/stores/DOES-NOT-EXIST/heartbeat")

    assert response.status_code == 404
    assert response.json() == {"detail": "unknown store"}

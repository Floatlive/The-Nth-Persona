import asyncio

import httpx

from server.main import app


def request(path: str, host: str) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url=f"http://{host}",
        ) as client:
            return await client.get(path)

    return asyncio.run(run())


def test_health_accepts_loopback_hosts():
    response = request("/health", "127.0.0.1")

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_health_accepts_localhost():
    response = request("/health", "localhost")

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_health_rejects_untrusted_host():
    response = request("/health", "attacker.example")

    assert response.status_code == 400

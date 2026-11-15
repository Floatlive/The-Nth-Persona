import asyncio
import os

import httpx
import pytest
from fastapi import HTTPException

from server import main


def _post_chat(payload):
    async def run():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1",
        ) as client:
            return await client.post("/chat", json=payload)

    return asyncio.run(run())


def test_custom_api_base_cannot_consume_server_environment_key(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(main, "DATA_FILE", tmp_path / "current.json")
    monkeypatch.setattr(main, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "server-secret")

    response = _post_chat(
        {
            "provider": "deepseek",
            "message": "测试",
            "api_base": "http://127.0.0.1:18123",
            "model": "deepseek-flash",
        }
    )

    assert response.status_code == 400
    assert "自定义 API Base" in response.json()["detail"]


def test_legacy_nth_api_key_does_not_cross_provider_boundaries(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(main, "DATA_FILE", tmp_path / "current.json")
    monkeypatch.setattr(main, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setenv("NTH_API_KEY", "legacy-openai-secret")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = _post_chat(
        {
            "provider": "claude",
            "message": "测试",
            "model": "claude-sonnet-5-5",
        }
    )

    assert response.status_code == 400
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


@pytest.mark.parametrize(
    "api_base",
    [
        "https://api.example.com/v1?key=secret",
        "https://api.example.com/v1#fragment",
    ],
)
def test_api_base_rejects_query_and_fragment(api_base):
    with pytest.raises(HTTPException, match="查询参数或片段"):
        main.normalize_api_base(api_base)


def test_provider_defaults_are_exposed_without_credentials():
    async def run():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1",
        ) as client:
            return await client.get("/provider-defaults")

    response = asyncio.run(run())

    assert response.status_code == 200
    providers = response.json()["providers"]
    assert providers["claude"]["model"] == "claude-sonnet-5-5"
    assert providers["deepseek"]["model"] == "deepseek-flash"
    assert "api_key" not in str(providers).lower()
    assert all(name not in str(providers) for name in os.environ if name.endswith("_API_KEY"))

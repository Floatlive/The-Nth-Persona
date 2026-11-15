import asyncio
import json

import httpx
import pytest

from server import main
from server.activation import resolve_activation


@pytest.mark.parametrize(
    ("state", "provider", "conversation_id", "active"),
    [
        ({"enabled": False, "scope": "off"}, "codex", "one", False),
        ({"enabled": True, "scope": "global"}, "gemini", None, True),
        (
            {"enabled": True, "scope": "provider", "provider": "claude"},
            "claude",
            "one",
            True,
        ),
        (
            {"enabled": True, "scope": "provider", "provider": "claude"},
            "gemini",
            "one",
            False,
        ),
    ],
)
def test_activation_scope_matches_only_intended_target(
    state, provider, conversation_id, active
):
    assert resolve_activation(state, provider, conversation_id).active is active


def test_legacy_state_migrates_to_enabled_global(monkeypatch, tmp_path):
    current_file = tmp_path / "current.json"
    history_file = tmp_path / "history.json"
    current_file.write_text(
        json.dumps(
            {
                "user_id": "default",
                "persona": "minimalist",
                "name": "极简主义者",
                "switched_at": "2026-11-15T00:00:00+00:00",
                "version": 4,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "DATA_FILE", current_file)
    monkeypatch.setattr(main, "HISTORY_FILE", history_file)

    state = main.read_current()

    assert state["enabled"] is True
    assert state["scope"] == "global"
    assert state["provider"] is None
    assert state["conversation_id"] is None


@pytest.mark.parametrize(
    "legacy_fields",
    [
        {
            "enabled": False,
            "scope": "off",
            "provider": None,
            "conversation_id": None,
            "binding_pending": True,
            "binding_started_at": "2026-11-15T00:00:00+00:00",
        },
        {
            "enabled": True,
            "scope": "conversation",
            "provider": "codex",
            "conversation_id": "old-chat",
        },
    ],
)
def test_legacy_codex_conversation_state_migrates_to_off(
    monkeypatch, tmp_path, legacy_fields
):
    current_file = tmp_path / "current.json"
    history_file = tmp_path / "history.json"
    current_file.write_text(
        json.dumps(
            {
                "user_id": "default",
                "persona": "minimalist",
                "name": "极简主义者",
                "switched_at": "2026-11-15T00:00:00+00:00",
                "version": 4,
                **legacy_fields,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "DATA_FILE", current_file)
    monkeypatch.setattr(main, "HISTORY_FILE", history_file)

    state = main.read_current()

    assert state["enabled"] is False
    assert state["scope"] == "off"
    assert state["provider"] is None
    assert state["conversation_id"] is None
    assert state["version"] == 5
    assert "binding_pending" not in state
    assert "binding_started_at" not in state
    assert main.read_current()["version"] == 5


def test_enable_endpoint_sets_conversation_scope(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "DATA_FILE", tmp_path / "current.json")
    monkeypatch.setattr(main, "HISTORY_FILE", tmp_path / "history.json")

    async def run():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://127.0.0.1"
        ) as client:
            enabled = await client.post(
                "/enable",
                json={
                    "enabled": True,
                    "scope": "conversation",
                    "provider": "gemini",
                    "conversation_id": "chat-42",
                },
            )
            matching = await client.get(
                "/context",
                params={"provider": "gemini", "conversation_id": "chat-42"},
            )
            other = await client.get(
                "/context",
                params={"provider": "gemini", "conversation_id": "chat-99"},
            )
            return enabled, matching, other

    enabled, matching, other = asyncio.run(run())

    assert enabled.status_code == 200
    assert enabled.json()["current"]["scope"] == "conversation"
    assert matching.json()["active"] is True
    assert "极简主义者" not in matching.json()["additional_context"]
    assert matching.json()["persona"] == main.DEFAULT_PERSONA
    assert other.json()["active"] is False
    assert other.json()["additional_context"] == ""


def test_enable_rejects_conversation_scope_without_target(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "DATA_FILE", tmp_path / "current.json")
    monkeypatch.setattr(main, "HISTORY_FILE", tmp_path / "history.json")

    async def run():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://127.0.0.1"
        ) as client:
            return await client.post(
                "/enable",
                json={
                    "enabled": True,
                    "scope": "conversation",
                    "provider": "claude",
                },
            )

    response = asyncio.run(run())

    assert response.status_code == 422


@pytest.mark.parametrize("endpoint", ["/enable", "/switch"])
def test_activation_rejects_codex_conversation_scope(
    monkeypatch, tmp_path, endpoint
):
    monkeypatch.setattr(main, "DATA_FILE", tmp_path / "current.json")
    monkeypatch.setattr(main, "HISTORY_FILE", tmp_path / "history.json")

    payload = {
        "enabled": True,
        "scope": "conversation",
        "provider": "codex",
        "conversation_id": "chat-42",
    }
    if endpoint == "/switch":
        payload["persona"] = "minimalist"

    async def run():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://127.0.0.1"
        ) as client:
            return await client.post(endpoint, json=payload)

    response = asyncio.run(run())

    assert response.status_code == 422
    assert "Codex 暂不支持可靠锁定单个聊天" in response.text


def test_switch_rejects_conversation_scope_without_target(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "DATA_FILE", tmp_path / "current.json")
    monkeypatch.setattr(main, "HISTORY_FILE", tmp_path / "history.json")

    async def run():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://127.0.0.1"
        ) as client:
            return await client.post(
                "/switch",
                json={
                    "persona": "minimalist",
                    "enabled": True,
                    "scope": "conversation",
                    "provider": "claude",
                },
            )

    response = asyncio.run(run())

    assert response.status_code == 422


@pytest.mark.parametrize("endpoint", ["/enable", "/switch"])
def test_activation_rejects_enabled_off_scope(monkeypatch, tmp_path, endpoint):
    monkeypatch.setattr(main, "DATA_FILE", tmp_path / "current.json")
    monkeypatch.setattr(main, "HISTORY_FILE", tmp_path / "history.json")

    payload = {"enabled": True, "scope": "off"}
    if endpoint == "/switch":
        payload["persona"] = "minimalist"

    async def run():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://127.0.0.1"
        ) as client:
            return await client.post(endpoint, json=payload)

    response = asyncio.run(run())

    assert response.status_code == 422

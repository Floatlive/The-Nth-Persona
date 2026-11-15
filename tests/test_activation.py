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
        (
            {
                "enabled": True,
                "scope": "conversation",
                "provider": "codex",
                "conversation_id": "session-1",
            },
            "codex",
            "session-1",
            True,
        ),
        (
            {
                "enabled": True,
                "scope": "conversation",
                "provider": "codex",
                "conversation_id": "session-1",
            },
            "codex",
            None,
            False,
        ),
        (
            {
                "enabled": True,
                "scope": "conversation",
                "provider": "codex",
                "conversation_id": "session-1",
            },
            "codex",
            "session-2",
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

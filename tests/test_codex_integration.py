import asyncio
import json

import httpx

from server import main


HOOK_TOKEN = "test-hook-token"


def get_codex_context(conversation_id: str | None = None) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1",
        ) as client:
            return await client.get(
                "/codex/context",
                params={"conversation_id": conversation_id}
                if conversation_id
                else None,
            )

    return asyncio.run(run())


def post_codex_context(
    conversation_id: str | None,
    token: str = HOOK_TOKEN,
) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1",
        ) as client:
            return await client.post(
                "/codex/context",
                json={"conversation_id": conversation_id},
                headers={"X-Nth-Persona-Token": token},
            )

    return asyncio.run(run())


def begin_codex_binding() -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1",
        ) as client:
            return await client.post("/codex/bind")

    return asyncio.run(run())


def disable_persona() -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1",
        ) as client:
            return await client.post(
                "/enable",
                json={"enabled": False, "scope": "off"},
            )

    return asyncio.run(run())


def get_integration_status() -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1",
        ) as client:
            return await client.get("/integration/status")

    return asyncio.run(run())


def test_codex_context_uses_current_persona_and_separates_old_assistant_style(
    monkeypatch, tmp_path
):
    current_file = tmp_path / "current.json"
    history_file = tmp_path / "history.json"
    current_file.write_text(
        json.dumps(
            {
                "user_id": "default",
                "persona": "minimalist",
                "name": "极简主义者",
                "switched_at": "2026-11-14T00:00:00+00:00",
                "version": 7,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "DATA_FILE", current_file)
    monkeypatch.setattr(main, "HISTORY_FILE", history_file)

    response = get_codex_context()

    assert response.status_code == 200
    data = response.json()
    assert data["persona"] == "minimalist"
    assert data["name"] == "极简主义者"
    assert data["version"] == 7
    assert "系统、开发者指令和安全边界内" in data["additional_context"]
    assert "此前助手发言" in data["additional_context"]
    assert "不会删除现有聊天记录" in data["additional_context"]


def test_codex_context_recovers_unknown_persona_to_safe_default(monkeypatch, tmp_path):
    current_file = tmp_path / "current.json"
    history_file = tmp_path / "history.json"
    current_file.write_text(
        json.dumps({"persona": "../../unexpected", "version": 8}),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "DATA_FILE", current_file)
    monkeypatch.setattr(main, "HISTORY_FILE", history_file)

    response = get_codex_context()

    assert response.status_code == 200
    assert response.json()["persona"] == main.DEFAULT_PERSONA
    assert response.json()["version"] == 1


def test_integration_status_records_latest_codex_context_read(monkeypatch, tmp_path):
    current_file = tmp_path / "current.json"
    history_file = tmp_path / "history.json"
    current_file.write_text(
        json.dumps(
            {
                "user_id": "default",
                "persona": "xin-da-ya",
                "name": "信达雅",
                "switched_at": "2026-11-15T00:00:00+00:00",
                "version": 13,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "DATA_FILE", current_file)
    monkeypatch.setattr(main, "HISTORY_FILE", history_file)
    monkeypatch.setattr(main, "LAST_CODEX_READ", None, raising=False)
    monkeypatch.setattr(main, "current_codex_hook_token", lambda: HOOK_TOKEN)

    before = get_integration_status()
    context = post_codex_context("chat-13")
    after = get_integration_status()

    assert before.status_code == 200
    assert before.json()["codex"]["last_read_at"] is None
    assert context.status_code == 200
    assert after.status_code == 200
    data = after.json()
    assert data["current"]["persona"] == "xin-da-ya"
    assert data["current"]["version"] == 13
    assert data["codex"]["persona"] == "xin-da-ya"
    assert data["codex"]["version"] == 13
    assert data["codex"]["conversation_id"] == "chat-13"
    assert data["codex"]["last_read_at"].endswith("+00:00")


def test_codex_binding_ignores_old_read_and_disables_previous_global_scope(
    monkeypatch, tmp_path
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
                "version": 20,
                "enabled": True,
                "scope": "global",
                "provider": None,
                "conversation_id": None,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "DATA_FILE", current_file)
    monkeypatch.setattr(main, "HISTORY_FILE", history_file)
    monkeypatch.setattr(main, "LAST_CODEX_READ", None, raising=False)
    monkeypatch.setattr(main, "current_codex_hook_token", lambda: HOOK_TOKEN)

    assert post_codex_context("old-chat").json()["active"] is True

    pending = begin_codex_binding()
    stale_get = get_codex_context("old-chat")
    state = get_integration_status().json()["current"]

    assert pending.status_code == 200
    assert pending.json()["current"]["binding_pending"] is True
    assert stale_get.json()["active"] is False
    assert stale_get.json()["reason"] == "binding_pending"
    assert state["enabled"] is False
    assert state["scope"] == "off"
    assert state["conversation_id"] is None


def test_first_authenticated_hook_atomically_consumes_pending_binding(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(main, "DATA_FILE", tmp_path / "current.json")
    monkeypatch.setattr(main, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(main, "LAST_CODEX_READ", None, raising=False)
    monkeypatch.setattr(main, "current_codex_hook_token", lambda: HOOK_TOKEN)

    begin_codex_binding()
    target = post_codex_context("target-chat")
    other = post_codex_context("other-chat")
    state = get_integration_status().json()["current"]

    assert target.status_code == 200
    assert target.json()["active"] is True
    assert target.json()["reason"] == "conversation"
    assert other.status_code == 200
    assert other.json()["active"] is False
    assert other.json()["reason"] == "conversation_mismatch"
    assert state["binding_pending"] is False
    assert state["enabled"] is True
    assert state["scope"] == "conversation"
    assert state["provider"] == "codex"
    assert state["conversation_id"] == "target-chat"


def test_untrusted_hook_cannot_consume_pending_binding(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "DATA_FILE", tmp_path / "current.json")
    monkeypatch.setattr(main, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(main, "LAST_CODEX_READ", None, raising=False)
    monkeypatch.setattr(main, "current_codex_hook_token", lambda: HOOK_TOKEN)

    begin_codex_binding()
    rejected = post_codex_context("attacker-chat", token="wrong-token")
    state = get_integration_status().json()["current"]

    assert rejected.status_code == 401
    assert state["binding_pending"] is True
    assert state["conversation_id"] is None


def test_disabling_during_pending_prevents_late_hook_from_reenabling(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(main, "DATA_FILE", tmp_path / "current.json")
    monkeypatch.setattr(main, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(main, "LAST_CODEX_READ", None, raising=False)
    monkeypatch.setattr(main, "current_codex_hook_token", lambda: HOOK_TOKEN)

    begin_codex_binding()
    disabled = disable_persona()
    late = post_codex_context("late-chat")
    state = get_integration_status().json()["current"]

    assert disabled.status_code == 200
    assert disabled.json()["current"]["binding_pending"] is False
    assert late.status_code == 200
    assert late.json()["active"] is False
    assert state["enabled"] is False
    assert state["scope"] == "off"
    assert state["conversation_id"] is None

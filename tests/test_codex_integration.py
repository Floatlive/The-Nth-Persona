import asyncio
import json

import httpx

from server import main


def get_codex_context() -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1",
        ) as client:
            return await client.get("/codex/context")

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

    before = get_integration_status()
    context = get_codex_context()
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
    assert data["codex"]["last_read_at"].endswith("+00:00")

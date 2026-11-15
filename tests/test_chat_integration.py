import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

from server import main


class _ChatHandler(BaseHTTPRequestHandler):
    request_body = None

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        type(self).request_body = json.loads(self.rfile.read(length))
        body = json.dumps(
            {"choices": [{"message": {"content": "已按当前人格回答"}}]}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def test_chat_sends_current_persona_as_first_system_message(monkeypatch, tmp_path):
    current_file = tmp_path / "current.json"
    history_file = tmp_path / "history.json"
    current_file.write_text(
        json.dumps(
            {
                "user_id": "default",
                "persona": "minimalist",
                "name": "极简主义者",
                "switched_at": "2026-11-15T00:00:00+00:00",
                "version": 12,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "DATA_FILE", current_file)
    monkeypatch.setattr(main, "HISTORY_FILE", history_file)

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), _ChatHandler)
    thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    try:
        async def run():
            transport = httpx.ASGITransport(app=main.app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://127.0.0.1",
            ) as client:
                return await client.post(
                    "/chat",
                    json={
                        "message": "现在怎么做？",
                        "history": [
                            {"role": "assistant", "content": "旧人格的冗长回答"}
                        ],
                        "api_key": "test-key",
                        "api_base": f"http://127.0.0.1:{upstream.server_port}",
                        "model": "test-model",
                        "persona_version": 12,
                    },
                )

        response = asyncio.run(run())

        assert response.status_code == 200, response.text
        messages = _ChatHandler.request_body["messages"]
        assert messages[0]["role"] == "system"
        assert "极简主义者" in messages[0]["content"]
        assert "系统、开发者指令和安全边界内" in messages[0]["content"]
        assert "不要沿用或模仿此前助手发言中的旧人格" in messages[0]["content"]
        assert messages[1] == {
            "role": "assistant",
            "content": "旧人格的冗长回答",
        }
        assert messages[2] == {"role": "user", "content": "现在怎么做？"}
    finally:
        upstream.shutdown()
        upstream.server_close()


def test_chat_drops_old_persona_assistant_messages_after_switch(monkeypatch, tmp_path):
    current_file = tmp_path / "current.json"
    history_file = tmp_path / "history.json"
    current_file.write_text(
        json.dumps(
            {
                "user_id": "default",
                "persona": "minimalist",
                "name": "极简主义者",
                "switched_at": "2026-11-15T00:00:00+00:00",
                "version": 12,
                "previous": "sharp-advisor",
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

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), _ChatHandler)
    thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    try:
        async def run():
            transport = httpx.ASGITransport(app=main.app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://127.0.0.1",
            ) as client:
                return await client.post(
                    "/chat",
                    json={
                        "provider": "deepseek",
                        "message": "继续",
                        "history": [
                            {"role": "user", "content": "用户事实"},
                            {
                                "role": "assistant",
                                "content": "旧人格观点",
                                "persona_version": 11,
                            },
                            {
                                "role": "assistant",
                                "content": "当前人格观点",
                                "persona_version": 12,
                            },
                            {"role": "assistant", "content": "未标记旧回复"},
                        ],
                        "api_key": "test-key",
                        "api_base": f"http://127.0.0.1:{upstream.server_port}",
                        "model": "test-model",
                        "persona_version": 12,
                    },
                )

        response = asyncio.run(run())

        assert response.status_code == 200, response.text
        contents = [
            item["content"] for item in _ChatHandler.request_body["messages"]
        ]
        assert "用户事实" in contents
        assert "当前人格观点" in contents
        assert "旧人格观点" not in contents
        assert "未标记旧回复" not in contents
    finally:
        upstream.shutdown()
        upstream.server_close()

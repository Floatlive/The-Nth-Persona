import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "codex-plugin" / "hooks" / "user_prompt_submit.ps1"


class _ContextHandler(BaseHTTPRequestHandler):
    last_path = None
    last_token = None
    last_body = None

    def do_POST(self):
        type(self).last_path = self.path
        type(self).last_token = self.headers.get("X-Nth-Persona-Token")
        length = int(self.headers.get("Content-Length", "0"))
        type(self).last_body = json.loads(self.rfile.read(length) or b"{}")
        if self.path != "/codex/context":
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps(
            {
                "persona": "minimalist",
                "name": "极简主义者",
                "version": 9,
                "additional_context": "当前生效人格是「极简主义者」。只输出必要内容。",
            },
            ensure_ascii=False,
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


@pytest.mark.skipif(os.name != "nt", reason="需要 Windows PowerShell 5.1")
def test_hook_reads_custom_port_from_user_runtime_config(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ContextHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        local_app_data = tmp_path / "LocalAppData"
        config_dir = local_app_data / "TheNthPersona"
        config_dir.mkdir(parents=True)
        config_dir.joinpath("service.json").write_text(
            json.dumps(
                {
                    "codex_context_url": (
                        f"http://127.0.0.1:{server.server_port}/codex/context"
                    ),
                    "codex_hook_token": "runtime-token",
                }
            ),
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["LOCALAPPDATA"] = str(local_app_data)
        env.pop("NTH_PERSONA_CODEX_URL", None)

        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(HOOK),
            ],
            input='{"prompt":"test"}',
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        assert result.returncode == 0, result.stderr
        output = json.loads(result.stdout.strip())
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "极简主义者" in context
        assert "只输出必要内容" in context
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.skipif(os.name != "nt", reason="需要 Windows PowerShell 5.1")
def test_hook_passes_session_id_as_diagnostic_metadata_only(tmp_path):
    _ContextHandler.last_path = None
    _ContextHandler.last_token = None
    _ContextHandler.last_body = None
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ContextHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        local_app_data = tmp_path / "LocalAppData"
        config_dir = local_app_data / "TheNthPersona"
        config_dir.mkdir(parents=True)
        config_dir.joinpath("service.json").write_text(
            json.dumps({"codex_hook_token": "runtime-token"}),
            encoding="utf-8",
        )
        env["LOCALAPPDATA"] = str(local_app_data)
        env["NTH_PERSONA_CODEX_URL"] = (
            f"http://127.0.0.1:{server.server_port}/codex/context"
        )
        env.pop("NTH_PERSONA_CODEX_TOKEN", None)

        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(HOOK),
            ],
            input=json.dumps({"session_id": "chat / 42", "prompt": "不要记录我"}),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert _ContextHandler.last_path == "/codex/context"
        assert _ContextHandler.last_token == "runtime-token"
        assert _ContextHandler.last_body == {"conversation_id": "chat / 42"}
        assert "不要记录我" not in result.stdout
    finally:
        server.shutdown()
        server.server_close()


class _InactiveContextHandler(BaseHTTPRequestHandler):
    last_path = None

    def do_POST(self):
        type(self).last_path = self.path
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        body = json.dumps(
            {
                "active": False,
                "additional_context": "",
                "reason": "conversation_mismatch",
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


@pytest.mark.skipif(os.name != "nt", reason="需要 Windows PowerShell 5.1")
def test_hook_returns_empty_result_when_persona_is_not_active(tmp_path):
    _InactiveContextHandler.last_path = None
    server = ThreadingHTTPServer(("127.0.0.1", 0), _InactiveContextHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["LOCALAPPDATA"] = str(tmp_path / "LocalAppData")
        env["NTH_PERSONA_CODEX_URL"] = (
            f"http://127.0.0.1:{server.server_port}/codex/context"
        )
        env["NTH_PERSONA_CODEX_TOKEN"] = "env-token"
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(HOOK),
            ],
            input=json.dumps({"session_id": "other-chat", "prompt": "test"}),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert _InactiveContextHandler.last_path == "/codex/context", (
            result.stdout,
            result.stderr,
        )
        assert json.loads(result.stdout) == {}
    finally:
        server.shutdown()
        server.server_close()

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
    def do_GET(self):
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
                    )
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

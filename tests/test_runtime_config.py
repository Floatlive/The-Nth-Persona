import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_config_cli_writes_codex_context_url(tmp_path):
    local_app_data = tmp_path / "LocalAppData"
    env = os.environ.copy()
    env["LOCALAPPDATA"] = str(local_app_data)

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "server" / "runtime_config.py"),
            "--url",
            "http://127.0.0.1:8010",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    config_path = local_app_data / "TheNthPersona" / "service.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data["base_url"] == "http://127.0.0.1:8010"
    assert data["codex_context_url"] == "http://127.0.0.1:8010/codex/context"
    assert data["updated_at"].endswith("+00:00")

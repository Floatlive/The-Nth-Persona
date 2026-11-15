from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import tempfile
from urllib.parse import urlparse


def runtime_config_path() -> Path:
    if os.name == "nt":
        base = os.getenv("LOCALAPPDATA")
        if base:
            return Path(base) / "TheNthPersona" / "service.json"
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    base = Path(xdg_config) if xdg_config else Path.home() / ".config"
    return base / "the-nth-persona" / "service.json"


def normalize_local_base_url(raw: str) -> str:
    value = raw.strip().rstrip("/")
    parsed = urlparse(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or parsed.username
        or parsed.password
        or not parsed.port
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("服务地址必须是带端口的本机 HTTP 地址")
    return value


def write_runtime_config(base_url: str, config_path: Path | None = None) -> Path:
    normalized = normalize_local_base_url(base_url)
    path = config_path or runtime_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    hook_token = ""
    if path.exists():
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
            hook_token = str(current.get("codex_hook_token", "")).strip()
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            hook_token = ""
    if len(hook_token) < 32:
        hook_token = secrets.token_urlsafe(32)
    data = {
        "base_url": normalized,
        "codex_context_url": f"{normalized}/codex/context",
        "codex_hook_token": hook_token,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    return path


def read_codex_hook_token(config_path: Path | None = None) -> str:
    path = config_path or runtime_config_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ""
    if not isinstance(data, dict):
        return ""
    return str(data.get("codex_hook_token", "")).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    print(write_runtime_config(args.url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import json
import os
import socket
import subprocess
import sys
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from server.version import APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "server" / "service_probe.py"


@contextmanager
def version_server(payload):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/version":
                self.send_error(404)
                return
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def run_probe(url):
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, str(PROBE), url],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=5,
        check=False,
    )


def test_probe_accepts_matching_service():
    with version_server({"name": "第N人格", "version": APP_VERSION}) as url:
        result = run_probe(url)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "status": "current",
        "name": "第N人格",
        "version": APP_VERSION,
    }


def test_probe_rejects_older_project_service():
    with version_server({"name": "第N人格", "version": "0.2.9"}) as url:
        result = run_probe(url)

    assert result.returncode == 2, result.stderr
    assert json.loads(result.stdout) == {
        "status": "conflict",
        "name": "第N人格",
        "version": "0.2.9",
    }


def test_application_version_is_043_and_rejects_042_service():
    assert APP_VERSION == "0.4.3"

    with version_server({"name": "第N人格", "version": "0.4.2"}) as url:
        result = run_probe(url)

    assert result.returncode == 2, result.stderr
    assert json.loads(result.stdout) == {
        "status": "conflict",
        "name": "第N人格",
        "version": "0.4.2",
    }


def test_probe_reports_unavailable_service():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        url = f"http://127.0.0.1:{listener.getsockname()[1]}"

    result = run_probe(url)

    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout) == {"status": "unavailable"}

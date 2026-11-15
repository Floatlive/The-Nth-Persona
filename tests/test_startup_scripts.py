import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(os.name != "nt", reason="需要 Windows PowerShell 5.1")
def test_windows_startup_script_parses_in_windows_powershell():
    script = ROOT / "open.ps1"
    command = (
        f"$source = Get-Content -Raw -LiteralPath '{script}'; "
        "[scriptblock]::Create($source) | Out-Null"
    )

    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr.decode(errors="replace")

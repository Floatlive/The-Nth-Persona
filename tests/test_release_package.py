import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_release.py"


def git(repo, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def test_release_builder_archives_explicit_ref_and_excludes_local_state(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Release Test")
    git(repo, "config", "user.email", "release-test@example.invalid")

    files = {
        "open.py": "print('start')",
        "server/main.py": "app = True",
        "cold-executor/SKILL.md": "# Persona",
        "index.html": "<main>UI</main>",
        ".env": "SECRET=not-for-release",
        ".env.example": "API_KEY=",
        ".runtime/state.json": "{}",
        ".venv/pyvenv.cfg": "home = local",
        "server/data/current.json": "{}",
    }
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    git(repo, "add", ".")
    git(repo, "commit", "-qm", "candidate")
    git(repo, "tag", "v0.4.3")
    (repo / "open.py").write_text("print('uncommitted')", encoding="utf-8")

    output = tmp_path / "dist"
    result = subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--repo",
            str(repo),
            "--ref",
            "v0.4.3",
            "--output-dir",
            str(output),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    archive = output / "the-nth-persona-v0.4.3.zip"
    assert archive.is_file()
    with zipfile.ZipFile(archive) as package:
        names = set(package.namelist())

    assert "open.py" in names
    assert "server/main.py" in names
    assert "cold-executor/SKILL.md" in names
    assert "index.html" in names
    assert ".env.example" in names
    assert not any(
        name == ".env"
        or name.startswith((".runtime/", ".venv/", "server/data/"))
        for name in names
    )
    assert (repo / "open.py").read_text(encoding="utf-8") == "print('uncommitted')"


def test_release_builder_fails_for_unknown_ref(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")

    result = subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--repo",
            str(repo),
            "--ref",
            "missing-tag",
            "--output-dir",
            str(tmp_path / "dist"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert not list((tmp_path / "dist").glob("*.zip"))

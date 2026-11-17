import argparse
import io
import subprocess
import tarfile
import zipfile
from pathlib import Path, PurePosixPath


EXCLUDED_PARTS = {
    ".runtime",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "data",
}


def excluded(path):
    parts = PurePosixPath(path).parts
    return (
        path == ".env"
        or any(
            part.startswith(".env.") and part != ".env.example"
            for part in parts
        )
        or any(part in EXCLUDED_PARTS for part in parts)
        or path.endswith((".pyc", ".pyo"))
    )


def build(repo, ref, output_dir):
    resolved = subprocess.run(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    archive = subprocess.run(
        ["git", "archive", "--format=tar", resolved],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout

    version = ref.removeprefix("v")
    if not version or any(char not in "0123456789." for char in version):
        raise ValueError("Release ref must use a version tag such as v0.4.3")

    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"the-nth-persona-v{version}.zip"
    temporary = destination.with_suffix(".zip.tmp")
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as source:
            with zipfile.ZipFile(
                temporary, "w", compression=zipfile.ZIP_DEFLATED
            ) as package:
                for entry in source:
                    if not entry.isfile() or excluded(entry.name):
                        continue
                    content = source.extractfile(entry)
                    if content is not None:
                        package.writestr(entry.name, content.read())
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def main():
    parser = argparse.ArgumentParser(
        description="Build a clean source ZIP from a committed Git release ref."
    )
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--ref", required=True, help="Version tag, for example v0.4.3")
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    args = parser.parse_args()
    print(build(args.repo.resolve(), args.ref, args.output_dir.resolve()))


if __name__ == "__main__":
    main()

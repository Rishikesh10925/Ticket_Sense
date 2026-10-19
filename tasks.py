"""Cross-platform task runner. `make <task>` calls this on Linux/macOS/CI; on Windows
(no make by default) run `python tasks.py <task>` directly.

    python tasks.py setup       install backend (+ai, dev) and frontend dependencies
    python tasks.py up          start db, api and web with Docker Compose
    python tasks.py lint        ruff + mypy + frontend lint
    python tasks.py test        ai/ unit tests, then backend tests (needs Postgres)
    python tasks.py openapi     write docs/openapi.json from the running app
    python tasks.py reproduce   regenerate every evaluation table and figure
    python tasks.py demo        seed demo users and sample tickets
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"


def run(*cmd: str, cwd: Path = ROOT) -> None:
    print(f"$ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=cwd, shell=sys.platform == "win32" and cmd[0] in {"npm", "npx"})
    if result.returncode != 0:
        sys.exit(result.returncode)


def uv_python(*args: str, cwd: Path = ROOT) -> None:
    run("uv", "run", "--project", str(BACKEND), "python", *args, cwd=cwd)


def setup() -> None:
    run("uv", "sync", "--extra", "ai", "--extra", "dev", cwd=BACKEND)
    run("npm", "ci", cwd=ROOT / "frontend")


def up() -> None:
    run("docker", "compose", "up", "-d", "--build")


def lint() -> None:
    run("uvx", "ruff@0.14.0", "check", "backend", "ai", "data")
    targets = ["ai/generation/llm.py"] + (["ai/evaluation"] if (ROOT / "ai" / "evaluation").exists() else [])
    run("uvx", "mypy@1.18.2", "--ignore-missing-imports", "--follow-imports=silent", *targets)
    run("npm", "run", "lint", cwd=ROOT / "frontend")


def test() -> None:
    uv_python("-m", "pytest", "-q", "ai/tests")
    run("uv", "run", "pytest", "-q", cwd=BACKEND)


def openapi() -> None:
    code = "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))"
    out = subprocess.run(
        ["uv", "run", "python", "-c", code], cwd=BACKEND, capture_output=True, text=True, check=True
    ).stdout
    json.loads(out)  # fail loudly on anything that isn't the spec
    (ROOT / "docs" / "openapi.json").write_text(out, encoding="utf-8")
    print("wrote docs/openapi.json")


def reproduce() -> None:
    entry = ROOT / "ai" / "evaluation" / "reproduce.py"
    if not entry.exists():
        sys.exit("ai/evaluation/reproduce.py does not exist yet")
    uv_python(str(entry))


def demo() -> None:
    run("uv", "run", "python", "-m", "app.scripts.seed_demo_users", cwd=BACKEND)


TASKS = {f.__name__: f for f in (setup, up, lint, test, openapi, reproduce, demo)}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in TASKS:
        print(__doc__)
        sys.exit(1)
    if shutil.which("uv") is None and sys.argv[1] != "up":
        sys.exit("uv is required: https://docs.astral.sh/uv/")
    TASKS[sys.argv[1]]()

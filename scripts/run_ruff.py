from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUFF_CONFIG = PROJECT_ROOT / "backend" / "pyproject.toml"
TARGETS = (
    PROJECT_ROOT / "backend" / "app",
    PROJECT_ROOT / "backend" / "tests",
    PROJECT_ROOT / "simulator" / "simulator",
    PROJECT_ROOT / "simulator" / "tests",
    PROJECT_ROOT / "scripts" / "run_ruff.py",
    PROJECT_ROOT / "scripts" / "verify_simulator_smoke.py",
    PROJECT_ROOT / "scripts" / "tests",
)


def main() -> int:
    missing = [path for path in (RUFF_CONFIG, *TARGETS) if not path.exists()]
    if missing:
        for path in missing:
            print(f"Ruff target is missing: {path}", file=sys.stderr)
        return 2

    ruff = shutil.which("ruff")
    if ruff is None:
        print(
            "Ruff executable was not found. Install backend development dependencies first.",
            file=sys.stderr,
        )
        return 127

    command = [
        ruff,
        "check",
        "--no-cache",
        "--config",
        str(RUFF_CONFIG),
        *(str(path) for path in TARGETS),
    ]
    return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

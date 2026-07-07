#!/usr/bin/env python3
"""Run ruff and pytest after Python file edits."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    ruff = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "services", "tests", "mcp"],
        cwd=ROOT,
    )
    pytest = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q"],
        cwd=ROOT,
    )
    sys.exit(ruff.returncode or pytest.returncode)

if __name__ == "__main__":
    main()

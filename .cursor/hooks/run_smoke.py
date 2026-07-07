#!/usr/bin/env python3
"""Smoke test: quick CLI import check, optional discover dry-run via JOBHUNT_FULL_SMOKE=1."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    help_check = subprocess.run(
        [sys.executable, "-m", "services.orchestrator.cli", "discover", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if help_check.returncode != 0:
        sys.stderr.write(help_check.stderr or "jobhunt CLI smoke check failed\n")
        sys.exit(help_check.returncode)

    if os.environ.get("JOBHUNT_FULL_SMOKE") == "1":
        discover = subprocess.run(
            [sys.executable, "-m", "services.orchestrator.cli", "discover", "--dry-run"],
            cwd=ROOT,
        )
        sys.exit(discover.returncode)

    sys.exit(0)

if __name__ == "__main__":
    main()

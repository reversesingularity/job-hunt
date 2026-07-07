"""Validate master CV path utility."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.tailoring.fact_bank import (
    FactBankError,
    _expand_skills,
    load_fact_bank,
    validate_fact_bank,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate data/master_cv.json against JSON Resume schema"
    )
    ap.add_argument("path", nargs="?", default="data/master_cv.json")
    args = ap.parse_args()
    p = Path(args.path)
    if not p.exists():
        print(f"MISSING: {p}\nCopy data/master_cv.example.json and fill with verified facts.")
        return 1
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        validate_fact_bank(data)
        cv = load_fact_bank(p)
        skill_count = len(_expand_skills(cv.get("skills", [])))
        print(f"OK: {p} — {cv['basics']['name']} ({skill_count} skills)")
        return 0
    except FactBankError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"INVALID: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

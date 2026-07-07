"""Deterministic tailoring tests."""

import json
from pathlib import Path

from services.tailoring.deterministic import build_reports
from services.tailoring.fact_bank import normalize_to_internal

FIXTURE = Path(__file__).parent / "fixtures" / "master_cv.json"


def test_build_reports_no_fabrication():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cv = normalize_to_internal(data)
    jd = "We need SQL Python reporting power bi data analyst defence"
    cov, cv_md, pct, gaps, summary = build_reports(cv, jd)
    assert "sql" in cov.lower() or "SQL" in cv_md
    assert pct >= 0
    assert "Test Candidate" in cv_md
    assert "Fabricated Skill XYZ" not in cv_md

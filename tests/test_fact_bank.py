"""Fact bank validation tests."""

import json
from pathlib import Path

import pytest

from services.tailoring.fact_bank import load_fact_bank, normalize_to_internal, validate_fact_bank

FIXTURE = Path(__file__).parent / "fixtures" / "master_cv.json"


def test_validate_fixture():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    validate_fact_bank(data)


def test_normalize_internal_ids():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    internal = normalize_to_internal(data)
    assert internal["name"] == "Test Candidate"
    assert internal["experience"][0]["id"] == "work_0"
    assert internal["experience"][0]["bullets"][0]["id"] == "work_0_b0"


def test_load_fact_bank_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("MASTER_CV_PATH", str(tmp_path / "missing.json"))
    from services import config
    config.MASTER_CV_PATH = str(tmp_path / "missing.json")
    with pytest.raises(Exception):
        load_fact_bank()

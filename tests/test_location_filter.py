"""Location filter tests."""

import pytest

from services.scoring.location_filter import matches_location, parse_location_filter


def test_parse_location_filter():
    assert parse_location_filter("au,nz") == ["au", "nz"]
    assert parse_location_filter(None) is None


def test_parse_unknown_code():
    with pytest.raises(ValueError, match="Unknown location"):
        parse_location_filter("us")


def test_matches_au_location():
    assert matches_location(
        "Sydney, New South Wales, Australia",
        "greenhouse",
        codes=["au"],
    )


def test_matches_nz_adzuna_source():
    assert matches_location(
        "Some City",
        "adzuna:nz",
        codes=["nz"],
    )


def test_us_location_rejected_for_au_nz():
    assert not matches_location(
        "Costa Mesa, California, United States",
        "greenhouse",
        codes=["au", "nz"],
    )


def test_auckland_matches_nz():
    assert matches_location(
        "Auckland CBD, Auckland",
        "adzuna:nz",
        codes=["nz"],
    )

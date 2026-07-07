"""Filter jobs by country/region codes (e.g. au, nz)."""

from __future__ import annotations

import re

LOCATION_TERMS: dict[str, list[str]] = {
    "au": [
        "australia",
        "sydney",
        "melbourne",
        "brisbane",
        "canberra",
        "adelaide",
        "perth",
        "queensland",
        "victoria",
        "new south wales",
        "western australia",
        "tasmania",
        "northern territory",
        "australian capital territory",
        "nsw",
        "qld",
        "wa",
        "sa",
        "nt",
        "act",
        "hobart",
        "darwin",
        "gold coast",
        "newcastle",
    ],
    "nz": [
        "new zealand",
        " nz",
        "nz,",
        "(nz)",
        "auckland",
        "wellington",
        "christchurch",
        "hamilton",
        "tauranga",
        "dunedin",
        "queenstown",
        "palmerston north",
        "mount wellington",
        "manukau",
    ],
}


def parse_location_filter(value: str | None) -> list[str] | None:
    """Parse 'au,nz' into ['au', 'nz']. Returns None if unset."""
    if not value or not value.strip():
        return None
    codes = [c.strip().lower() for c in value.split(",") if c.strip()]
    unknown = [c for c in codes if c not in LOCATION_TERMS]
    if unknown:
        valid = ", ".join(sorted(LOCATION_TERMS))
        raise ValueError(f"Unknown location code(s): {unknown}. Valid: {valid}")
    return codes or None


def _term_in_location(term: str, loc: str) -> bool:
    """Match location terms without substring false positives (e.g. 'nt' in 'States')."""
    t = term.lower()
    if len(t) <= 3:
        return bool(re.search(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", loc))
    return t in loc


def matches_location(
    location: str | None,
    source: str | None,
    *,
    codes: list[str],
) -> bool:
    """True if posting location or Adzuna source matches any requested code."""
    loc = (location or "").lower()
    src = (source or "").lower()

    for code in codes:
        if code == "nz" and src.startswith("adzuna:nz"):
            return True
        if code == "au" and src.startswith("adzuna:au"):
            return True
        for term in LOCATION_TERMS[code]:
            if _term_in_location(term, loc):
                return True
    return False

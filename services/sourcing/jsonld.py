"""Schema.org JSON-LD JobPosting extraction from public career pages."""

from __future__ import annotations

import re

import extruct
import httpx
from w3lib.html import get_base_url

HEADERS = {"User-Agent": "JobHunt/1.0 (personal job search)"}


def extract_job_posting(url: str) -> dict | None:
    """Fetch a public career page and extract JobPosting JSON-LD."""
    try:
        r = httpx.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
        r.raise_for_status()
        base = get_base_url(r.text, url)
        data = extruct.extract(r.text, base_url=base, syntaxes=["json-ld"])
        for item in data.get("@graph", data) if isinstance(data, dict) else []:
            pass
        items = data if isinstance(data, list) else [data]
        for block in items:
            if isinstance(block, dict):
                found = _find_job_posting(block)
                if found:
                    return _normalise(found, url)
        # extruct returns dict keyed by syntax
        if isinstance(data, dict):
            for syntax_items in data.values():
                if not isinstance(syntax_items, list):
                    continue
                for item in syntax_items:
                    found = _find_job_posting(item)
                    if found:
                        return _normalise(found, url)
    except Exception as e:
        print(f"  ! JSON-LD extract failed for {url}: {e}")
    return None


def _find_job_posting(obj: dict) -> dict | None:
    if obj.get("@type") == "JobPosting":
        return obj
    if "@graph" in obj:
        for g in obj["@graph"]:
            if isinstance(g, dict) and g.get("@type") == "JobPosting":
                return g
    return None


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _normalise(jp: dict, url: str) -> dict:
    org = jp.get("hiringOrganization") or {}
    company = org.get("name", "") if isinstance(org, dict) else str(org)
    loc = jp.get("jobLocation") or {}
    location = ""
    if isinstance(loc, dict):
        addr = loc.get("address") or {}
        location = addr.get("addressLocality", "") if isinstance(addr, dict) else str(loc)
    return {
        "source": "jsonld",
        "company": company,
        "title": jp.get("title", ""),
        "location": location,
        "url": jp.get("url") or url,
        "description": _clean(jp.get("description", "")),
        "raw": jp,
    }

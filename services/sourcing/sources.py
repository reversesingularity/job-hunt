"""
Source connectors. Every function returns normalised posting dicts:

    {"source", "company", "title", "location", "url", "description", "raw"}

All primary sources are public, read-only APIs.
"""
from __future__ import annotations

import html
import os
import re

import requests

from services import config

TIMEOUT = 20
HEADERS = {"User-Agent": "JobHunt/1.0 (personal job search)"}


def _company_label(source: str, board: str) -> str:
    if source == "greenhouse":
        return config.GREENHOUSE_COMPANY_NAMES.get(board, board)
    return board


def _clean(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def from_greenhouse(board: str) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    out = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        for job in data.get("jobs", []):
            posting = {
                "source": "greenhouse",
                "company": _company_label("greenhouse", board),
                "title": job.get("title", ""),
                "location": (job.get("location") or {}).get("name", ""),
                "url": job.get("absolute_url", ""),
                "description": _clean(job.get("content", "")),
                "raw": job,
            }
            out.append(posting)
    except Exception as e:
        print(f"  ! greenhouse:{board} failed ({e})")
    return out


def from_lever(org: str) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{org}?mode=json"
    out = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        for job in r.json():
            cats = job.get("categories", {}) or {}
            posting = {
                "source": "lever",
                "company": org,
                "title": job.get("text", ""),
                "location": cats.get("location", ""),
                "url": job.get("hostedUrl", ""),
                "description": _clean(job.get("descriptionPlain", "")),
                "raw": job,
            }
            out.append(posting)
    except Exception as e:
        print(f"  ! lever:{org} failed ({e})")
    return out


def from_ashby(board: str) -> list[dict]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{board}"
    out = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        for job in data.get("jobs", []):
            loc = job.get("location", "")
            if isinstance(loc, dict):
                loc = loc.get("name", "")
            posting = {
                "source": "ashby",
                "company": board,
                "title": job.get("title", ""),
                "location": loc,
                "url": job.get("jobUrl") or job.get("applyUrl", ""),
                "description": _clean(job.get("descriptionPlain", job.get("description", ""))),
                "raw": job,
            }
            out.append(posting)
    except Exception as e:
        print(f"  ! ashby:{board} failed ({e})")
    return out


def from_adzuna(
    country: str, query: str, app_id: str, app_key: str, pages: int = 1
) -> list[dict]:
    out = []
    for page in range(1, pages + 1):
        url = (
            f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
            f"?app_id={app_id}&app_key={app_key}"
            f"&results_per_page=50&what={requests.utils.quote(query)}"
            f"&content-type=application/json"
        )
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            for job in r.json().get("results", []):
                posting = {
                    "source": f"adzuna:{country}",
                    "company": (job.get("company") or {}).get("display_name", ""),
                    "title": job.get("title", ""),
                    "location": (job.get("location") or {}).get("display_name", ""),
                    "url": job.get("redirect_url", ""),
                    "description": _clean(job.get("description", "")),
                    "raw": job,
                }
                out.append(posting)
        except Exception as e:
            print(f"  ! adzuna:{country}:{query} failed ({e})")
            break
    return out


def adzuna_keys() -> tuple[str | None, str | None]:
    return os.environ.get("ADZUNA_APP_ID"), os.environ.get("ADZUNA_APP_KEY")


def dedupe(postings: list[dict]) -> list[dict]:
    seen: set[str | tuple] = set()
    out = []
    for p in postings:
        key = p.get("url") or (p.get("company"), p.get("title"), p.get("location"))
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def gather_all() -> list[dict]:
    postings: list[dict] = []
    print("Fetching sources...")
    for board in config.GREENHOUSE_BOARDS:
        got = from_greenhouse(board)
        print(f"  greenhouse:{board} -> {len(got)}")
        postings.extend(got)
    for org in config.LEVER_ORGS:
        got = from_lever(org)
        print(f"  lever:{org} -> {len(got)}")
        postings.extend(got)
    for board in config.ASHBY_BOARDS:
        got = from_ashby(board)
        print(f"  ashby:{board} -> {len(got)}")
        postings.extend(got)

    app_id, app_key = adzuna_keys()
    if app_id and app_key:
        queries = list(dict.fromkeys(config.ADZUNA_QUERIES + config.ADZUNA_DEFENCE_QUERIES))
        for country in config.ADZUNA_COUNTRIES:
            for q in queries:
                got = from_adzuna(country, q, app_id, app_key)
                print(f"  adzuna:{country}:{q} -> {len(got)}")
                postings.extend(got)
    else:
        print("  (Adzuna skipped — set ADZUNA_APP_ID and ADZUNA_APP_KEY)")
    return dedupe(postings)

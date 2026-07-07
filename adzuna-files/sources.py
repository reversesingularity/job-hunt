"""
Source connectors. Every function returns a list of normalised posting dicts:

    {"source", "company", "title", "location", "url", "description"}

All three sources are public, read-only APIs. Nothing here scrapes a site or
touches LinkedIn — this is the terms-of-service-clean design we agreed on.
"""
import os
import re
import html
import requests

TIMEOUT = 20
HEADERS = {"User-Agent": "JobScout/1.0 (personal job search)"}


def _clean(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)        # strip HTML tags
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def from_greenhouse(board: str):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    out = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        for job in r.json().get("jobs", []):
            out.append({
                "source": "greenhouse",
                "company": board,
                "title": job.get("title", ""),
                "location": (job.get("location") or {}).get("name", ""),
                "url": job.get("absolute_url", ""),
                "description": _clean(job.get("content", "")),
            })
    except Exception as e:
        print(f"  ! greenhouse:{board} failed ({e})")
    return out


def from_lever(org: str):
    url = f"https://api.lever.co/v0/postings/{org}?mode=json"
    out = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        for job in r.json():
            cats = job.get("categories", {}) or {}
            out.append({
                "source": "lever",
                "company": org,
                "title": job.get("text", ""),
                "location": cats.get("location", ""),
                "url": job.get("hostedUrl", ""),
                "description": _clean(job.get("descriptionPlain", "")),
            })
    except Exception as e:
        print(f"  ! lever:{org} failed ({e})")
    return out


def from_adzuna(country: str, query: str, app_id: str, app_key: str, pages: int = 1):
    out = []
    for page in range(1, pages + 1):
        url = (f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
               f"?app_id={app_id}&app_key={app_key}"
               f"&results_per_page=50&what={requests.utils.quote(query)}"
               f"&content-type=application/json")
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            for job in r.json().get("results", []):
                out.append({
                    "source": f"adzuna:{country}",
                    "company": (job.get("company") or {}).get("display_name", ""),
                    "title": job.get("title", ""),
                    "location": (job.get("location") or {}).get("display_name", ""),
                    "url": job.get("redirect_url", ""),
                    "description": _clean(job.get("description", "")),
                })
        except Exception as e:
            print(f"  ! adzuna:{country}:{query} failed ({e})")
            break
    return out


def adzuna_keys():
    return os.environ.get("ADZUNA_APP_ID"), os.environ.get("ADZUNA_APP_KEY")

"""End-to-end pipeline orchestration."""

from __future__ import annotations

import csv
import re

from dotenv import load_dotenv

from services import config
from services.db import init_db, list_shortlist, save_score, save_tailored, upsert_job
from services.rendering import render_outputs
from services.scoring import score_posting
from services.sourcing import gather_all
from services.tailoring import (
    FactBankError,
    draft_cover_letter,
    load_fact_bank,
    normalize_to_internal,
    tailor_cv,
)


def discover(dry_run: bool = False) -> list[dict]:
    load_dotenv()
    init_db()
    postings = gather_all()
    print(f"\nTotal fetched: {len(postings)}")
    if dry_run:
        return postings
    ids = []
    for p in postings:
        job_id = upsert_job(p)
        ids.append(job_id)
    print(f"Persisted {len(ids)} jobs to database")
    return postings


def score_all(location_codes: list[str] | None = None) -> list[dict]:
    init_db()
    postings = gather_all()
    for p in postings:
        job_id = upsert_job(p)
        result = score_posting(p)
        save_score(job_id, result)

    shortlist = list_shortlist(location_codes=location_codes)
    print(f"Scored {len(postings)} jobs; shortlist has {len(shortlist)} qualifying")
    if location_codes:
        print(f"  (location filter: {','.join(location_codes)})")
    return shortlist


def tailor_job(job_id: int) -> dict:
    init_db()
    from services.db import get_job

    job = get_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")

    raw_cv = load_fact_bank()
    cv = normalize_to_internal(raw_cv)
    coverage_md, cv_md, pct, gaps, summary = tailor_cv(cv, job.get("description") or "")

    stem = re.sub(r"[^a-z0-9]+", "_", f"{job['company']}_{job['title']}".lower())[:40]
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cov_path = config.OUTPUT_DIR / f"coverage_{stem}.md"
    cov_path.write_text(coverage_md, encoding="utf-8")

    md_path, pdf_path = render_outputs(cv_md, raw_cv, stem)
    save_tailored(job_id, pct, gaps, md_path, pdf_path, md_path.replace(".md", ".html"), summary)

    cover = draft_cover_letter(cv, job, gaps)
    cl_path = config.OUTPUT_DIR / f"cover_letter_{stem}.md"
    cl_path.write_text(cover, encoding="utf-8")

    return {
        "job_id": job_id,
        "coverage_pct": pct,
        "gaps": gaps,
        "coverage_path": str(cov_path),
        "cv_md_path": md_path,
        "pdf_path": pdf_path,
        "cover_letter_path": str(cl_path),
    }


def run_pipeline(
    top: int = 10,
    dry_run: bool = False,
    location_codes: list[str] | None = None,
) -> None:
    if dry_run:
        discover(dry_run=True)
        return

    try:
        load_fact_bank()
    except FactBankError as e:
        print(f"ERROR: {e}")
        return

    discover()
    shortlist = score_all(location_codes=location_codes)
    loc_label = f" [{','.join(location_codes)}]" if location_codes else ""
    print(f"\nShortlist{loc_label}: {len(shortlist)} jobs")

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = config.OUTPUT_DIR / "shortlist.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# Job shortlist ({len(shortlist)} roles{loc_label})\n\n")
        for i, p in enumerate(shortlist[:top], 1):
            f.write(f"## {i}. {p['title']} — {p['company']}\n")
            f.write(f"- **Fit score:** {p['score']}\n")
            f.write(f"- **Location:** {p.get('location') or 'n/a'}\n")
            f.write(f"- **Why:** {'; '.join(p['reasons'])}\n")
            f.write(f"- **Link:** {p.get('url')}\n\n")

    csv_path = config.OUTPUT_DIR / "shortlist.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "score", "title", "company", "location", "url"])
        for p in shortlist[:top]:
            w.writerow([
                p["id"], p["score"], p["title"], p["company"],
                p.get("location"), p.get("url"),
            ])

    print(f"Wrote {md_path} and {csv_path}")

    for p in shortlist[:top]:
        print(f"\nTailoring job {p['id']}: {p['title']} @ {p['company']}")
        try:
            result = tailor_job(p["id"])
            print(f"  Coverage: {result['coverage_pct']}%  PDF: {result.get('pdf_path')}")
        except Exception as e:
            print(f"  ! Tailoring failed: {e}")

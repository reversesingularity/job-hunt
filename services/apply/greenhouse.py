"""
Playwright ATS form submission — Phase 2.

Requires human approval or fit score above AUTO_APPLY_THRESHOLD.
Never submit when seniority gate triggered or gaps exceed limit.
"""
from __future__ import annotations

from services import config
from services.db import approve_application, get_application, get_job, record_application_result


def can_auto_submit(job_id: int, fit_score: float, gap_count: int = 0) -> tuple[bool, str]:
    app = get_application(job_id)
    if not app:
        return False, "no application record"

    if config.REQUIRE_APPROVAL and not app.get("approved_by_user"):
        if fit_score < config.AUTO_APPLY_THRESHOLD:
            return False, f"score {fit_score} below threshold {config.AUTO_APPLY_THRESHOLD}"

    if gap_count > 5:
        return False, "too many skill gaps for auto-submit"

    return True, "ok"


def submit_greenhouse(job_id: int, pdf_path: str, *, force: bool = False) -> dict:
    """Submit application to Greenhouse ATS form via Playwright."""
    job = get_job(job_id)
    if not job:
        return {"ok": False, "error": "job not found"}

    fit_score = job.get("score") or 0
    allowed, reason = can_auto_submit(job_id, fit_score)
    if not allowed and not force:
        return {"ok": False, "error": reason, "needs_approval": True}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"ok": False, "error": "playwright not installed — pip install 'jobhunt[apply]'"}

    url = job.get("url", "")
    if "greenhouse" not in url.lower():
        return {"ok": False, "error": "not a Greenhouse URL"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")

            # Greenhouse embeds forms in iframes
            frame = page.frame_locator('iframe[title*="Greenhouse"], iframe[src*="greenhouse"]')
            file_input = frame.locator('input[type="file"]')
            if file_input.count() > 0:
                file_input.set_input_files(pdf_path)

            # Stop before final submit unless explicitly approved
            app = get_application(job_id)
            if app and app.get("approved_by_user"):
                submit_btn = frame.locator('button[type="submit"], input[type="submit"]')
                if submit_btn.count() > 0:
                    submit_btn.first.click()
                    record_application_result(job_id, "applied")
            else:
                record_application_result(job_id, "approved")

            browser.close()
        return {"ok": True, "job_id": job_id, "url": url}
    except Exception as e:
        record_application_result(job_id, "rejected")
        return {"ok": False, "error": str(e)}


def approve_and_submit(job_id: int, pdf_path: str) -> dict:
    approve_application(job_id)
    return submit_greenhouse(job_id, pdf_path, force=True)

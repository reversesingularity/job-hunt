"""SQLite persistence layer."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from services import config

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "db" / "schema.sql"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_conn() as conn:
        conn.executescript(sql)


def audit(event: str, payload: dict[str, Any] | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO audit_log (event, payload_json) VALUES (?, ?)",
            (event, json.dumps(payload or {})),
        )


def upsert_job(posting: dict[str, Any]) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO jobs (source, company, title, location, url, description, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title = excluded.title,
                location = excluded.location,
                description = excluded.description,
                fetched_at = datetime('now'),
                raw_json = excluded.raw_json
            RETURNING id
            """,
            (
                posting.get("source", ""),
                posting.get("company", ""),
                posting.get("title", ""),
                posting.get("location"),
                posting.get("url"),
                posting.get("description"),
                json.dumps(posting.get("raw", posting)),
            ),
        )
        row = cur.fetchone()
        job_id = row[0]
        conn.execute(
            """
            INSERT INTO applications (job_id, status) VALUES (?, 'discovered')
            ON CONFLICT(job_id) DO NOTHING
            """,
            (job_id,),
        )
        return job_id


def save_score(job_id: int, result: dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO job_scores (job_id, score, reasons_json, matched_skills_json,
                                    too_senior, title_match)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                score = excluded.score,
                reasons_json = excluded.reasons_json,
                matched_skills_json = excluded.matched_skills_json,
                too_senior = excluded.too_senior,
                title_match = excluded.title_match,
                scored_at = datetime('now')
            """,
            (
                job_id,
                result["score"],
                json.dumps(result["reasons"]),
                json.dumps(result.get("matched_skills", [])),
                1 if result.get("too_senior") else 0,
                1 if result.get("title_match") else 0,
            ),
        )
        conn.execute(
            "UPDATE applications SET status = 'scored', fit_score = ? WHERE job_id = ?",
            (result["score"], job_id),
        )


def save_tailored(
    job_id: int,
    coverage_pct: float,
    gaps: list[str],
    cv_md_path: str,
    pdf_path: str | None,
    html_path: str | None,
    summary_line: str,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tailored_outputs
                (job_id, coverage_pct, gaps_json, cv_md_path, pdf_path, html_path, summary_line)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                coverage_pct,
                json.dumps(gaps),
                cv_md_path,
                pdf_path,
                html_path,
                summary_line,
            ),
        )
        conn.execute(
            "UPDATE applications SET status = 'tailored' WHERE job_id = ?",
            (job_id,),
        )
        return cur.lastrowid or 0


def list_shortlist(
    limit: int = 40,
    min_score: float | None = None,
    location_codes: list[str] | None = None,
) -> list[dict[str, Any]]:
    from services.scoring.location_filter import matches_location

    threshold = min_score if min_score is not None else config.SCORE_THRESHOLD
    fetch_limit = limit * 15 if location_codes else limit
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT j.id, j.source, j.company, j.title, j.location, j.url,
                   j.description, s.score, s.reasons_json, s.matched_skills_json
            FROM jobs j
            JOIN job_scores s ON s.job_id = j.id
            WHERE s.score >= ? AND s.too_senior = 0
            ORDER BY s.score DESC
            LIMIT ?
            """,
            (threshold, fetch_limit),
        ).fetchall()
    out = []
    for r in rows:
        item = {
            "id": r["id"],
            "source": r["source"],
            "company": r["company"],
            "title": r["title"],
            "location": r["location"],
            "url": r["url"],
            "description": r["description"],
            "score": r["score"],
            "reasons": json.loads(r["reasons_json"] or "[]"),
            "matched_skills": json.loads(r["matched_skills_json"] or "[]"),
        }
        if location_codes and not matches_location(
            item["location"], item["source"], codes=location_codes
        ):
            continue
        out.append(item)
        if len(out) >= limit:
            break
    return out


def get_job(job_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT j.*, s.score, s.reasons_json, s.matched_skills_json
            FROM jobs j
            LEFT JOIN job_scores s ON s.job_id = j.id
            WHERE j.id = ?
            """,
            (job_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "source": row["source"],
        "company": row["company"],
        "title": row["title"],
        "location": row["location"],
        "url": row["url"],
        "description": row["description"],
        "score": row["score"],
        "reasons": json.loads(row["reasons_json"] or "[]") if row["reasons_json"] else [],
        "matched_skills": json.loads(row["matched_skills_json"] or "[]")
        if row["matched_skills_json"]
        else [],
    }


def approve_application(job_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE applications SET status = 'approved', approved_by_user = 1
            WHERE job_id = ?
            """,
            (job_id,),
        )
    audit("application_approved", {"job_id": job_id})


def record_application_result(job_id: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE applications SET status = ?, applied_at = datetime('now')
            WHERE job_id = ?
            """,
            (status, job_id),
        )
    audit("application_result", {"job_id": job_id, "status": status})


def get_application(job_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM applications WHERE job_id = ?",
            (job_id,),
        ).fetchone()
    return dict(row) if row else None

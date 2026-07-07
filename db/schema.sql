-- JobHunt SQLite schema (Postgres-compatible naming for future migration)

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT,
    url TEXT UNIQUE,
    description TEXT,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS job_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    score REAL NOT NULL,
    reasons_json TEXT NOT NULL,
    matched_skills_json TEXT,
    too_senior INTEGER NOT NULL DEFAULT 0,
    title_match INTEGER NOT NULL DEFAULT 0,
    scored_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(job_id)
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'discovered',
    fit_score REAL,
    approved_by_user INTEGER NOT NULL DEFAULT 0,
    applied_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(job_id)
);

CREATE TABLE IF NOT EXISTS tailored_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    coverage_pct REAL,
    gaps_json TEXT,
    cv_md_path TEXT,
    pdf_path TEXT,
    html_path TEXT,
    summary_line TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    payload_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_job_scores_score ON job_scores(score DESC);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);

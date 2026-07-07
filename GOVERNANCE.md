# Governance

This document defines how JobHunt and its portfolio subprojects are operated, what data is trusted, and what agents and contributors must never do.

## Scope

| Component | Purpose | Sensitive data |
|-----------|---------|------------------|
| **JobHunt core** (`services/`, `mcp/`) | Discover, score, tailor, render job applications | User fact bank, API keys, application state |
| **FNB tracker** (`fnb-tracker/`) | PMO demo — Future Naval Base Tranche 1a | None (synthetic) |
| **DE&I PMO** (`dei-pmo-dashboard/`) | PMO demo — horizontal infrastructure portfolio | None (synthetic) |
| **Interview Buddy** (`packages/interview-buddy/`) | Phase 3 scaffold | TBD |

## Ethics (non-negotiable)

These rules apply to all code, agents, and documentation in this repository:

1. **Never fabricate** skills, employers, dates, certifications, or metrics in CV tailoring or cover letters.
2. Tailoring may only **reorder, restructure, and emphasize** verified facts from `data/master_cv.json`.
3. Surface skill **gaps honestly**; recommend cover letter framing, learning plans, or stretch-role assessment where appropriate.
4. Do **not** scrape behind login walls, bypass CAPTCHAs, or extract PII from job boards.
5. Auto-submit (Phase 2) requires **explicit human approval** unless configured thresholds and governance checks pass.

## Data classification

| Class | Examples | Git policy |
|-------|----------|------------|
| **Secret** | `.env`, API keys, MotherDuck tokens | Never commit |
| **Personal** | `data/master_cv.json`, `jobhunt.db`, `output/` | Gitignored |
| **Synthetic demo** | DuckDB/CSV from `generate_*_data.py` | CSV may commit; DuckDB regenerated locally |
| **Public reference** | DEPP 2025 programme shape, project names in demos | Committed |

## Sourcing priority

1. Public ATS APIs (Greenhouse, Lever, Ashby, Adzuna)
2. Schema.org JSON-LD `JobPosting` on public career pages
3. Stealth browser fallback (Camoufox/Nodriver/SeleniumBase) — **no authenticated sessions**

## Agent and automation rules

Cursor rules in `.cursor/rules/` encode project constraints. Hooks in `.cursor/hooks.json` run ruff + pytest after Python edits and a lightweight CLI smoke check on agent stop.

Agents must:

- Read `GOVERNANCE.md` and `project-context.mdc` before modifying tailoring or sourcing code
- Not add secrets to committed files (use `.env` and environment variables)
- Not weaken the fact validator or scoring explainability without explicit user approval

## PMO dashboard disclaimers

Both Streamlit dashboards:

- Reflect **published programme parameters** (DEPP 2025, Budget 25 where cited)
- Use **100% synthetic** schedule, cost, risk, and performance data
- Are **not affiliated with or endorsed by** NZDF or any government agency
- Exist as portfolio demonstrations of EVM-style delivery tracking

## Decision log

| Date | Decision |
|------|----------|
| 2026 | Slice 1 MVP: discover → score → tailor → PDF; SQLite state; MCP tools |
| 2026 | AU/NZ location filter via `--location au,nz` |
| 2026 | FNB + DE&I dashboards as sibling apps sharing chart palette and DuckDB pattern |
| 2026 | Phase 2 apply deferred; human-in-the-loop required |

## Changes to this document

Material governance changes should be reflected here and in `.cursor/rules/project-context.mdc` in the same PR or commit series.

# Governance

This document defines how JobHunt and its portfolio subprojects are operated, what data is trusted, and what agents and contributors must never do.

## Scope

| Component | Purpose | Sensitive data |
|-----------|---------|------------------|
| **JobHunt core** (`services/`, `mcp/`) | Discover, score, tailor, render job applications | User fact bank, API keys, application state |
| **FNB tracker** (`fnb-tracker/`) | PMO demo — Future Naval Base Tranche 1a | None (synthetic) |
| **DE&I PMO** (`dei-pmo-dashboard/`) | PMO demo — horizontal infrastructure portfolio; also published as standalone repo [reversesingularity/dei-pmo-dashboard](https://github.com/reversesingularity/dei-pmo-dashboard) | Synthetic delivery figures; OIA reference PDFs are © Crown Copyright (public release) |
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
| **Crown Copyright (OIA)** | `dei-pmo-dashboard/docs/oia-reference/*.pdf` from OIA-2025-5483 | May commit for portfolio reference; **not** MIT-licensed; always attribute; never imply NZDF endorsement |

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

### DE&I PMO — security clearance vs Crown Copyright

The DE&I tactical dashboard reports (Oct 2024, Jan 2025, Mar 2025) were **publicly released** under the Official Information Act 1982 as **OIA-2025-5483**. Because NZDF released them through the OIA (with protected material withheld), they are **unclassified**. Hosting or citing those releases does **not** violate NZSIS / PSR / NZISM protective-security rules.

**Crown Copyright still applies.** Publishing unclassified OIA material is not a free licence to reuse Crown works without attribution and emblem rules:

| Rule | Requirement |
|------|-------------|
| Attribution | Caption UI and docs with: *Sourced from publicly available Official Information Act (OIA) release OIA-2025-5483. © Crown Copyright.* |
| Creative Commons | Where a release is CC BY 4.0, attribute the Crown (NZDF) when copying/displaying |
| Standard Crown Copyright | If no CC grant, Defence instructions generally require CDF permission before other-purpose reproduction |
| Emblems | Do **not** use the NZDF logo or NZ Government coat of arms in a way that suggests official representation or endorsement (*Flags, Emblems, and Names Protection Act 1981*) |

The live DE&I Streamlit app must keep the OIA caption visible in the **main header** and **sidebar**. Reference PDFs live under `dei-pmo-dashboard/docs/oia-reference/` (standalone repo: same path).

## Decision log

| Date | Decision |
|------|----------|
| 2026 | Slice 1 MVP: discover → score → tailor → PDF; SQLite state; MCP tools |
| 2026 | AU/NZ location filter via `--location au,nz` |
| 2026 | FNB + DE&I dashboards as sibling apps sharing chart palette and DuckDB pattern |
| 2026 | Phase 2 apply deferred; human-in-the-loop required |
| 2026-07-26 | Fact banks (`data/master_cv.json` canonical + `cv-files/master_cv.yml`) refreshed with verified facts for the NZDF-2607025 application: SAP HR+SRM end-user, DSSG base-access/ID-card duty, early roles (Bank of America, PLDT), Spark vendor names, CONFIDENTIAL clearance, education years, driver's licence. Sources: prior CVs, GitHub README, and candidate confirmation — consistent with the Ethics "never fabricate / verified facts only" rule. |
| 2026-07-26 | Published standalone public repo [reversesingularity/dei-pmo-dashboard](https://github.com/reversesingularity/dei-pmo-dashboard) with comprehensive README (charts, architecture diagrams, OIA/Crown Copyright section), MIT for code, Crown notice for OIA PDFs. |
| 2026-07-26 | Confirmed portfolio hosting of OIA-2025-5483 materials is clear from NZSIS/security standpoint; mandatory OIA caption + no NZDF emblems as endorsement. Caption added to live DE&I Streamlit UI (header + sidebar). |

## Changes to this document

Material governance changes should be reflected here and in `.cursor/rules/project-context.mdc` in the same PR or commit series.

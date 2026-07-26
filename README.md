# JobHunt — Autonomous & Honest Job Acquisition Engine

API-first job discovery, transparent fit scoring, and **non-deceptive** CV tailoring for NZ/AU defence and data bridge roles — plus standalone **PMO portfolio dashboards** built on the same delivery-tracking stack.

## Principles

- **Never fabricate**: tailoring only reorders and emphasizes verified facts from `data/master_cv.json`
- **API-first sourcing**: Greenhouse, Lever, Ashby, Adzuna — no login scraping
- **Explainable scoring**: every fit point maps to a human-readable reason
- **Human-in-the-loop apply** (Phase 2): auto-submit only above score threshold with approval

See [GOVERNANCE.md](GOVERNANCE.md) for ethics, data classification, and secret handling.

## Quickstart

```powershell
# 1. Install Python dependencies (from repo root)
pip install -e ".[dev]"

# 2. Copy env and add keys
copy .env.example .env
# Edit .env: ADZUNA_APP_ID, ADZUNA_APP_KEY, OPENAI_API_KEY (optional)

# 3. Place your canonical fact bank (JSON Resume schema)
copy data\master_cv.example.json data\master_cv.json
# Edit data/master_cv.json with your verified facts

# 4. Validate fact bank
python -m services.tailoring.validate_cv data/master_cv.json

# 5. Run the pipeline
jobhunt run --top 10 --location au,nz
```

### Step-by-step CLI

```bash
jobhunt discover
jobhunt score --location au,nz
jobhunt tailor --job-id 1
jobhunt render --job-id 1
```

## Slice 1 Pipeline

```
Discover → Score → Tailor → PDF
```

- **Sourcing**: Greenhouse (Rocket Lab, Anduril), Adzuna role + defence contractor queries
- **Scoring**: weighted 2.0× hard skills / 1.5× title / 1.0× context; `--location au,nz` filter
- **Tailoring**: LLM STAR reorder (T=0.1) + fact validator + deterministic fallback
- **Rendering**: ATS HTML/PDF with embedded JSON Resume block

Outputs land in `output/` (`shortlist.md`, `shortlist.csv`, `coverage_*.md`, `tailored_cv_*.pdf`, `cover_letter_*.md`). State is tracked in SQLite (`jobhunt.db`).

## MCP Server

```bash
python -m mcp.server
```

Tools: `get_applicant_context`, `list_shortlist` (with `location`), `tailor_for_job`, `draft_cover_letter`

## Portfolio dashboards (PMO demos)

Standalone Streamlit apps using DuckDB + Plotly on a validated dark-navy palette (`#0e1b2c`). All delivery figures are **synthetic**; programme shape reflects published DEPP 2025 parameters.

| App | Path | Description |
|-----|------|-------------|
| **FNB Tranche 1 Tracker** | [`fnb-tracker/`](fnb-tracker/) | Six Tranche 1a Devonport projects; capital/operating envelopes; stage gates |
| **DE&I Horizontal PMO** | [`dei-pmo-dashboard/`](dei-pmo-dashboard/) · [standalone GitHub](https://github.com/reversesingularity/dei-pmo-dashboard) | 141-project portfolio; 24/45/72 priority split; 5×5 risk matrix; OIA-2025-5483 reference PDFs with Crown Copyright attribution |

```powershell
cd fnb-tracker
pip install -r requirements.txt
python generate_fnb_data.py
streamlit run app.py

cd ..\dei-pmo-dashboard
pip install -r requirements.txt
python generate_mock_data.py
streamlit run app.py
```

**DE&I attribution (required wherever OIA materials or the demo framing appear):**

> *Sourced from publicly available Official Information Act (OIA) release OIA-2025-5483. © Crown Copyright.*

Security vs copyright detail: [GOVERNANCE.md — PMO dashboard disclaimers](GOVERNANCE.md#pmo-dashboard-disclaimers). Do not use NZDF logos or government emblems as endorsement.
## Project layout

```
services/              Job pipeline (sourcing, scoring, tailoring, rendering, apply)
mcp/                   MCP tool server
db/                    SQLite schema
data/                  Fact bank (master_cv.json gitignored) + examples
scripts/               Utility scripts (placements preview, location analysis)
fnb-tracker/           FNB Tranche 1 Streamlit dashboard
dei-pmo-dashboard/     DE&I horizontal infrastructure Streamlit dashboard
packages/interview-buddy/   Phase 3 scaffold
tests/                 pytest suite
.cursor/               Agent rules, hooks, architecture plan
```

Legacy folders (`adzuna-files/`, `cv-files/`, `jd-datanalyst-files/`, `build-cv-files/`) are superseded by `services/` and kept for reference only.

## Development

```bash
pip install -e ".[dev]"
pytest tests -q
python -m ruff check services tests mcp
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for workflow and [`.cursor/plans/architecture.md`](.cursor/plans/architecture.md) for full architecture.

## Phase 2+

- **Stealth ingestion**: JSON-LD + Camoufox/Nodriver/SeleniumBase (`services/sourcing/stealth/`)
- **Auto-submit**: Playwright ATS forms with approval gates (`services/apply/`)
- **Interview Buddy**: Electron desktop companion (`packages/interview-buddy/`)

## Disclaimer

JobHunt is a personal job-acquisition tool. PMO dashboards use synthetic data and are not affiliated with or endorsed by NZDF. DE&I OIA reference materials remain © Crown Copyright (OIA-2025-5483). Do not commit secrets, API keys, or your canonical `master_cv.json`.

# Session handoff — DE&I PMO Dashboard

**Date:** 2026-07-26 (updated after landing + Railway deploy)  
**Primary repo:** https://github.com/reversesingularity/dei-pmo-dashboard  
**Live app:** https://dei-pmo.reversesingularity.com  
**Monorepo path:** `job-hunt/dei-pmo-dashboard/` (nested git; also mirrored under parent JobHunt)  
**Owner site:** https://reversesingularity.com (card id `dei-pmo`)

## What was completed

### Publish / docs (earlier same day)

1. **Standalone GitHub repo created and pushed** (`reversesingularity/dei-pmo-dashboard`, public, `main`).
2. **Comprehensive README** with portfolio tables, Mermaid diagrams, Plotly PNG gallery (`docs/assets/`), architecture / EVM / data-pipeline images, quickstart, and full **NZSIS vs Crown Copyright** section.
3. **OIA reference PDFs** filed under `docs/oia-reference/` (Oct 2024, Jan 2025, Mar 2025) with attribution README.
4. **MIT LICENSE** for code + Crown Copyright carve-out for OIA PDFs.
5. **Live Streamlit OIA caption** in `app.py` — main header *and* sidebar.
6. **Governance sync** in parent JobHunt: `GOVERNANCE.md`, `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `.cursor/rules/project-context.mdc`, `.cursor/plans/architecture.md`.

### Landing + deploy (later same day)

7. **Railway deploy** — Dockerfile Streamlit image; DuckDB regenerated at build; service `dei-pmo-dashboard`.
8. **Custom domain** `dei-pmo.reversesingularity.com` (CNAME + Railway verify TXT on Vercel DNS; SSL valid; HTTP 200).
9. **Landing card** registered and shipped on reversesingularity.com (`dei-pmo`, cyan accent).
10. **GitHub homepage** set to https://dei-pmo.reversesingularity.com

## Security / copyright stance (do not reverse)

| Topic | Verdict |
|-------|---------|
| NZSIS / PSR / NZISM | Clear — OIA-2025-5483 materials are publicly released / unclassified |
| Crown Copyright | Still applies — attribute always; CC BY only if the specific release grants it |
| Emblems | Never use NZDF logo or NZ coat of arms as endorsement |
| Synthetic data | All SPI/CPI/risk/schedule/cost figures remain mock (SEED=7) |

## How to run (local)

```powershell
cd f:\Projects\job-hunt\dei-pmo-dashboard
pip install -r requirements.txt
python generate_mock_data.py   # if data/dei.duckdb missing
streamlit run app.py           # often http://localhost:8501 or :8502
```

Optional README chart regen: `pip install kaleido` then `python scripts/export_readme_assets.py`.

## Deploy (Railway)

```powershell
cd f:\Projects\job-hunt\dei-pmo-dashboard
railway link   # project acceptable-dream / service dei-pmo-dashboard
railway up
```

Deploy assets (commit if not already on `main`):

| Path | Role |
|------|------|
| `Dockerfile` | Install deps, `generate_mock_data.py`, Streamlit on `$PORT` |
| `railway.toml` | DOCKERFILE builder + `/` healthcheck |
| `.dockerignore` | Skip docs/pdfs/venv; duckdb built in image |

## Key files

| Path | Role |
|------|------|
| `app.py` | Entry + **OIA captions** (must remain) |
| `config.py` | Portfolio shape, RAG/risk, palette |
| `generate_mock_data.py` | Seeded synthetic data |
| `views/*.py` | Overview / Risk / Financial tabs |
| `docs/assets/` | README gallery PNGs |
| `docs/oia-reference/` | Crown Copyright OIA PDFs |
| `README.md` | Public documentation |
| `HANDOFF.md` | This file |

## Parent JobHunt notes

- Ethics / fact-bank rules unchanged — never fabricate CV content.
- DE&I demo is a **portfolio / interview** artefact (DE&I Projects Officer / MacGyver Protocol / zero onboarding lag), not an official NZDF product.
- Landing handoff for the site card: `reversesingularity_landing/docs/SESSION-HANDOFF.md`

## Incident note (2026-07-26)

While adding the OIA PDF gitignore exception to the parent `job-hunt` repo, a bad `git add` pathspec briefly committed personal CV PDFs and `output/` tailored CVs to `reversesingularity/job-hunt`. They were **removed in a follow-up commit** (`d26bcb7`). They may still exist in git history of that commit range until history is purged if desired.

## Suggested next-session work

- [ ] Commit + push `Dockerfile`, `railway.toml`, `.dockerignore` to GitHub
- [ ] Optional: Railway ↔ GitHub auto-deploy; rename project `acceptable-dream` → `dei-pmo-dashboard`
- [ ] Confirm Streamlit still shows OIA caption after any UI polish
- [ ] Decide whether parent `job-hunt` should submodule or subtree-sync the standalone DE&I repo
- [ ] Remove leftover root `dashboard2.pdf` / `dashboard3.pdf` locks if still present
- [ ] Optional: purge `job-hunt` git history for commit `247c696` personal/output PDFs if required

## Do not

- Strip OIA captions from `app.py` or README
- Add NZDF/government logos to branding
- Present synthetic EVM figures as real NZDF delivery data
- Commit `.env`, `data/master_cv.json`, or secrets into either repo
- Commit personal CV PDFs or `output/` tailored PDFs (global `*.pdf` ignore; only `docs/oia-reference/*.pdf` is excepted)

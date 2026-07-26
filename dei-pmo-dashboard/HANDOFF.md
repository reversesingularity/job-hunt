# Session handoff — DE&I PMO Dashboard

**Date:** 2026-07-26  
**Primary repo:** https://github.com/reversesingularity/dei-pmo-dashboard  
**Monorepo path:** `job-hunt/dei-pmo-dashboard/` (nested git; also mirrored under parent JobHunt)  
**Owner site:** reversesingularity.com

## What was completed this session

1. **Standalone GitHub repo created and pushed** (`reversesingularity/dei-pmo-dashboard`, public, `main`).
2. **Comprehensive README** with portfolio tables, Mermaid diagrams, Plotly PNG gallery (`docs/assets/`), architecture / EVM / data-pipeline images, quickstart, and full **NZSIS vs Crown Copyright** section.
3. **OIA reference PDFs** filed under `docs/oia-reference/` (Oct 2024, Jan 2025, Mar 2025) with attribution README.
4. **MIT LICENSE** for code + Crown Copyright carve-out for OIA PDFs.
5. **Live Streamlit OIA caption** in `app.py` — main header *and* sidebar:

   > *Sourced from publicly available Official Information Act (OIA) release OIA-2025-5483. © Crown Copyright.*

6. **Governance sync** in parent JobHunt: `GOVERNANCE.md`, `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `.cursor/rules/project-context.mdc`, `.cursor/plans/architecture.md`.

## Security / copyright stance (do not reverse)

| Topic | Verdict |
|-------|---------|
| NZSIS / PSR / NZISM | Clear — OIA-2025-5483 materials are publicly released / unclassified |
| Crown Copyright | Still applies — attribute always; CC BY only if the specific release grants it |
| Emblems | Never use NZDF logo or NZ coat of arms as endorsement |
| Synthetic data | All SPI/CPI/risk/schedule/cost figures remain mock (SEED=7) |

## How to run

```powershell
cd f:\Projects\job-hunt\dei-pmo-dashboard
pip install -r requirements.txt
python generate_mock_data.py   # if data/dei.duckdb missing
streamlit run app.py           # often http://localhost:8501 or :8502
```

Optional README chart regen: `pip install kaleido` then `python scripts/export_readme_assets.py`.

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
- Parent decision log and data-classification table now include Crown Copyright / OIA class and standalone repo URL.

## Suggested next-session work

- [ ] Confirm Streamlit still shows OIA caption after any UI polish
- [ ] Wire demo screenshots or Streamlit Cloud / static host link into `reversesingularity.com` with the same caption
- [ ] Decide whether parent `job-hunt` should submodule or subtree-sync the standalone DE&I repo (currently nested `.git` inside monorepo path)
- [ ] Remove leftover root `dashboard2.pdf` / `dashboard3.pdf` locks if still present (canonical copies are in `docs/oia-reference/`)
- [ ] Optional: deploy Streamlit Community Cloud from the standalone repo
- [ ] Optional: add FNB tracker twin publish if desired for consistency

## Do not

- Strip OIA captions from `app.py` or README
- Add NZDF/government logos to branding
- Present synthetic EVM figures as real NZDF delivery data
- Commit `.env`, `data/master_cv.json`, or secrets into either repo
- Commit personal CV PDFs or `output/` tailored PDFs (global `*.pdf` ignore; only `docs/oia-reference/*.pdf` is excepted)

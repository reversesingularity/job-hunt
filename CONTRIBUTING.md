# Contributing

Thank you for improving JobHunt. This repo is primarily a personal job-acquisition workspace, but contributions to shared tooling, tests, and portfolio dashboards are welcome.

## Prerequisites

- Python 3.11+
- `pip install -e ".[dev]"` from the repository root
- Optional: Node.js for `npm run build-docx` (DOCX rendering)

## Setup

```powershell
git clone https://github.com/reversesingularity/job-hunt.git
cd job-hunt
pip install -e ".[dev]"
copy .env.example .env
copy data\master_cv.example.json data\master_cv.json
```

Do **not** commit `.env` or `data/master_cv.json`.

## Development workflow

1. Create a branch from `main`
2. Make focused changes — prefer minimal diffs
3. Run checks before opening a PR:

```bash
python -m ruff check services tests mcp
pytest tests -q
python -m services.tailoring.validate_cv data/master_cv.example.json
```

4. For dashboard changes, regenerate mock data and smoke-test Streamlit:

```powershell
cd dei-pmo-dashboard
python generate_mock_data.py
streamlit run app.py
```

## Commit messages

Use clear, imperative subjects focused on **why**:

- `Add AU/NZ location filter to shortlist MCP tool`
- `Fix ruff line length in validate_cv CLI`
- `Document DE&I PMO dashboard in root README`

## Pull request checklist

- [ ] No secrets, tokens, or personal CV data in the diff
- [ ] Tests pass (`pytest tests -q`)
- [ ] Ruff clean on touched Python paths
- [ ] README or GOVERNANCE updated if behaviour or ethics changed
- [ ] Synthetic-data disclaimers preserved for PMO dashboards
- [ ] DE&I changes keep OIA-2025-5483 Crown Copyright caption (UI + docs) and do not add NZDF/government emblems as endorsement
- [ ] If publishing the standalone DE&I app, sync https://github.com/reversesingularity/dei-pmo-dashboard as well as this monorepo path

## Code conventions

- Match existing patterns in `services/` (typed functions, repository-style DB access)
- Tailoring changes must preserve fact-bank validation (`services/tailoring/validator.py`)
- New sourcing must respect [GOVERNANCE.md](GOVERNANCE.md) API-first policy

## Reporting issues

For security concerns (leaked keys, scraping policy violations), see [SECURITY.md](SECURITY.md).

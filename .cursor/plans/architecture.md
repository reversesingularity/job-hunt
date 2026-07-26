# Job Acquisition Engine — Architecture



See [GOVERNANCE.md](../../GOVERNANCE.md) for ethics and data policy.



## Slice 1 (MVP): Discover → Score → Tailor → PDF



- **Fact bank**: `data/master_cv.json` (JSON Resume, user-supplied, gitignored)

- **Sourcing**: Greenhouse, Lever, Ashby, Adzuna APIs + defence contractor Adzuna queries

- **Scoring**: Weighted 2.0x / 1.5x / 1.0x with explainable reasons; `--location au,nz`

- **Tailoring**: LLM STAR reorder (T=0.1) + deterministic fallback + fact validator

- **Rendering**: ATS HTML/PDF with embedded JSON Resume block

- **State**: SQLite (`jobhunt.db`)

- **MCP**: `get_applicant_context`, `list_shortlist`, `tailor_for_job`, `draft_cover_letter`



## Portfolio dashboards (PMO demos)



Sibling Streamlit apps sharing DuckDB + Plotly + dark-navy palette:



| App | Data | Scale |

|-----|------|-------|

| `fnb-tracker/` | `data/fnb.duckdb` | 6 Tranche 1a projects |

| `dei-pmo-dashboard/` | `data/dei.duckdb` | 141 projects (24/45/72 priority) |



Regenerate with `generate_fnb_data.py` / `generate_mock_data.py`. All figures synthetic.



**DE&I standalone publish:** https://github.com/reversesingularity/dei-pmo-dashboard



- Comprehensive README + `docs/assets/` chart/architecture gallery

- OIA-2025-5483 PDFs in `docs/oia-reference/` (© Crown Copyright; not MIT)

- Live UI must show OIA caption in header + sidebar (`app.py`)

- Security stance: public OIA release → unclassified / not an NZSIS breach to cite; Crown Copyright + emblem rules still apply (see `GOVERNANCE.md`)



## Slice 2: Stealth + Auto-Submit



- JSON-LD Schema.org extraction

- Camoufox / Nodriver / SeleniumBase UC + proxy rotation

- Playwright Greenhouse submitter with approval/score gates



## Slice 3: Interview Buddy



- Electron desktop companion (scaffold only in Slice 1)



## Commands



```bash

jobhunt run --top 10 --location au,nz

python -m services.tailoring.validate_cv data/master_cv.json

python -m mcp.server

```



## Workspace



- Rules: `.cursor/rules/*.mdc`

- Hooks: `.cursor/hooks.json` (ruff + pytest on edit; CLI smoke on stop)

- Tasks: `.vscode/tasks.json` (manual lint/test/smoke)


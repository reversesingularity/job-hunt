# FNB Tranche 1 Delivery Tracker

A PMO-style delivery dashboard for **Tranche 1a of the Future Naval Base (FNB)
programme** — the regeneration of Devonport Naval Base, New Zealand's only
naval port (estimated at up to $4B over 35 years). Built as a portfolio piece
demonstrating tracking of complex, multi-tranche government infrastructure
delivery **on time, on budget, and in full**.

## What it shows

| Tab | Content |
|---|---|
| **Executive Summary** | Burn of the **$25.185M capital** and **$5.375M operating** Budget 25 envelopes (FY26–FY29), programme SPI/CPI health banner, budget burndown, per-project RAG table |
| **Schedule & Gates** | Gantt of design & enabling-works phases across all six projects, stage-gate diamonds, and the hard **Tranche 1b Construction DBC (FY2028/29)** funding gate |
| **Project Deep Dive** | Per-project EVM S-curve (PV/EV/AC), phase progress, stage-gate register |

## The six Tranche 1a projects

1. New Officer Training School facility (Narrow Neck)
2. Replacement Sea Safety Training Squadron facility
3. Replacement of Dry Dock Caisson Gates
4. Redevelopment of Stanley Bay Gate entrance
5. Temporary multi-purpose office spaces
6. Base-wide horizontal infrastructure network planning

## Quickstart

```powershell
cd fnb-tracker
pip install -r requirements.txt
python generate_fnb_data.py   # seeded mock data -> data/fnb.duckdb + CSVs
streamlit run app.py
```

## Architecture

```
generate_fnb_data.py   seeded mock-data generator (projects/phases/financials/milestones)
config.py              budget envelopes, programme dates, validated chart palette
data_access.py         DuckDB query layer + EVM aggregations (st.cache_data)
app.py                 entry point: sidebar filters, tabs
views/
  chart_theme.py       shared dark-navy Plotly chrome
  kpi.py               Tab 1 - executive summary
  gantt.py             Tab 2 - schedule & gates
  deep_dive.py         Tab 3 - project drill-down
.streamlit/config.toml dark theme
```

## EVM methodology

Monthly ledger per project and expense type carries **Planned Value**,
**Earned Value**, and **Actual Cost**. The dashboard derives
`SPI = EV / PV` and `CPI = EV / AC`; RAG status is `min(SPI, CPI)` against
0.95 (green) and 0.85 (amber) floors. The mock data is deliberately
imperfect — e.g. the caisson-gate design runs behind schedule on specialist
marine-engineering inputs — so variance reporting behaves like a real
portfolio.

## Factual basis & disclaimer

Programme scope, project list, budget envelopes ($25.185M capital, $5.375M
operating over FY26–FY29), and the FY2028/29 Tranche 1b detailed business
case milestone reflect published parameters from the **2025 Defence Estate
Portfolio Plan** and **Budget 25** Cabinet approvals. **All schedule, cost,
and performance figures are synthetic** (seeded random generation) and do not
represent actual NZDF delivery data. Not affiliated with or endorsed by NZDF.

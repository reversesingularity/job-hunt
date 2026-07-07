# DE&I Horizontal Infrastructure PMO Dashboard

A PMO-style delivery dashboard for the **Defence Estate & Infrastructure (DE&I)
horizontal infrastructure portfolio** — 141 projects across nine NZDF bases
(water, wastewater, stormwater, power, ICT, and roading). Built as a portfolio
piece demonstrating large-scale government infrastructure tracking **on time, on
budget, and in full**.

## What it shows

| Tab | Content |
|---|---|
| **Executive Overview** | Portfolio budget, spend-to-date, SPI/CPI, at-risk count, priority mix, budget by base, top-15 at-risk register |
| **Risk Management** | 5×5 likelihood × consequence matrix with zone banding, High & Extreme zone register |
| **Financial & Schedule** | Top-10 Gantt by budget, burndown envelope, per-project EVM table |

## Portfolio shape (DEPP 2025)

- **141 projects** total
- **24 Critical** / **45 High** / **72 Medium-Low** (44 Medium + 28 Low)
- Four pinned example projects:
  - Devonport HV Electrical Upgrade
  - Waiouru Wastewater Network
  - Papakura Potable Water Network
  - Whenuapai Stormwater Network

## Quickstart

```powershell
cd dei-pmo-dashboard
pip install -r requirements.txt
python generate_mock_data.py   # seeded mock data -> data/dei.duckdb + CSVs
streamlit run app.py
```

## Architecture

```
generate_mock_data.py   seeded mock-data generator (projects + financials)
config.py               portfolio shape, RAG/risk thresholds, chart palette
data_access.py          DuckDB query layer + EVM aggregations (st.cache_data)
app.py                  entry point: sidebar filters, tabs
views/
  chart_theme.py        shared dark-navy Plotly chrome
  overview.py           Tab 1 - executive overview
  risk.py               Tab 2 - 5×5 risk matrix + register
  financial.py          Tab 3 - Gantt, burndown, EVM table
.streamlit/config.toml  dark theme (#0e1b2c surface)
```

## EVM methodology

Monthly ledger per project carries **Planned Value**, **Earned Value**, and
**Actual Cost**. The dashboard derives `SPI = EV / PV` and `CPI = EV / AC`;
RAG status is `min(SPI, CPI)` against 0.95 (green) and 0.85 (amber) floors.
Risk scores are `likelihood × consequence` (1–25) banded into Low / Moderate /
High / Extreme zones.

## Factual basis & disclaimer

Portfolio scale (141 projects, 24/45/72 priority split), base locations, and
domain mix reflect published parameters from the **2025 Defence Estate Portfolio
Plan**. **All schedule, cost, performance, and risk figures are synthetic**
(seeded random generation) and do not represent actual NZDF delivery data. Not
affiliated with or endorsed by NZDF.

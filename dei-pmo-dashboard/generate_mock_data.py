"""Generate seeded mock delivery data for the DE&I horizontal infrastructure portfolio.

Writes a DuckDB database (data/dei.duckdb) with two tables - projects and
financials - plus CSV exports. Portfolio shape (141 projects; 24 Critical /
45 High / 72 Medium-Low across water, power, ICT and roading) reflects the
2025 Defence Estate Portfolio Plan; every delivery figure is synthetic.

Usage: python generate_mock_data.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import duckdb
import numpy as np
import pandas as pd

from config import (
    AS_AT_DATE,
    BASES,
    CSV_DIR,
    DATA_DIR,
    DB_PATH,
    DOMAINS,
    PORTFOLIO_START,
    PRIORITY_COUNTS,
    RAG_AMBER_FLOOR,
    RAG_GREEN_FLOOR,
    TOTAL_PROJECTS,
)

SEED = 7

ASSET_TEMPLATES: dict[str, tuple[str, ...]] = {
    "Water": ("Potable Water Network", "Water Treatment Plant", "Reservoir & Pump Station"),
    "Wastewater": ("Wastewater Network", "Wastewater Treatment Upgrade", "Sewer Main Renewal"),
    "Stormwater": ("Stormwater Network", "Stormwater Detention Basin", "Culvert Renewal"),
    "Power": ("HV Electrical Upgrade", "LV Reticulation Renewal", "Substation Replacement"),
    "ICT": ("Fibre Backbone", "ICT Duct Network", "Comms Room Resilience"),
    "Roading": ("Pavement Renewal", "Internal Roading Upgrade", "Hardstand Reconstruction"),
}

# The four DEPP example projects, pinned so they always appear in the data.
NAMED_PROJECTS: tuple[tuple[str, str, str, str, float], ...] = (
    ("Devonport HV Electrical Upgrade", "Devonport", "Power", "Critical", 42.0),
    ("Waiouru Wastewater Network", "Waiouru", "Wastewater", "Critical", 28.5),
    ("Papakura Potable Water Network", "Papakura", "Water", "High", 12.8),
    ("Whenuapai Stormwater Network", "Whenuapai", "Stormwater", "High", 9.6),
)

LIKELIHOOD_WEIGHTS: dict[str, tuple[float, ...]] = {
    "Critical": (0.05, 0.15, 0.30, 0.30, 0.20),
    "High": (0.10, 0.25, 0.35, 0.20, 0.10),
    "Medium": (0.20, 0.30, 0.30, 0.15, 0.05),
    "Low": (0.35, 0.35, 0.20, 0.08, 0.02),
}
CONSEQUENCE_WEIGHTS: dict[str, tuple[float, ...]] = {
    "Critical": (0.00, 0.05, 0.15, 0.40, 0.40),
    "High": (0.05, 0.10, 0.35, 0.35, 0.15),
    "Medium": (0.10, 0.30, 0.40, 0.15, 0.05),
    "Low": (0.35, 0.40, 0.20, 0.05, 0.00),
}
SPI_MEAN: dict[str, float] = {
    "Critical": 0.96, "High": 0.98, "Medium": 1.00, "Low": 1.00,
}


@dataclass(frozen=True)
class ProjectRow:
    """One generated portfolio project."""

    project_id: str
    name: str
    base: str
    domain: str
    priority: str
    budget_m: float
    start_date: date
    end_date: date
    spi: float
    cpi: float
    likelihood: int
    consequence: int


def _add_months(start: date, months: int) -> date:
    total = start.year * 12 + (start.month - 1) + months
    return date(total // 12, total % 12 + 1, 1)


def _rag_status(spi: float, cpi: float, end: date, as_at: date) -> str:
    if end <= as_at and min(spi, cpi) >= RAG_AMBER_FLOOR:
        return "Complete"
    worst = min(spi, cpi)
    if worst >= RAG_GREEN_FLOOR:
        return "On Track"
    if worst >= RAG_AMBER_FLOOR:
        return "At Risk"
    return "Behind"


def _pct_complete(start: date, end: date, spi: float, as_at: date) -> float:
    if start > as_at:
        return 0.0
    elapsed = (as_at - start).days / max((end - start).days, 1)
    return float(np.clip(elapsed * spi * 100.0, 0.0, 100.0))


def _budget(rng: np.random.Generator, priority: str) -> float:
    scale = {"Critical": 2.6, "High": 2.1, "Medium": 1.6, "Low": 1.1}[priority]
    return float(np.clip(rng.lognormal(mean=scale, sigma=0.55), 0.4, 60.0))


def _schedule(rng: np.random.Generator, budget_m: float) -> tuple[date, date]:
    start = _add_months(PORTFOLIO_START, int(rng.integers(0, 42)))
    months = int(np.clip(12 + budget_m * rng.uniform(0.6, 1.3), 12, 72))
    return start, _add_months(start, months)


def _performance(rng: np.random.Generator, priority: str) -> tuple[float, float]:
    spi = float(np.clip(rng.normal(SPI_MEAN[priority], 0.07), 0.72, 1.15))
    cpi = float(np.clip(rng.normal(0.99, 0.06), 0.75, 1.15))
    return spi, cpi


def _risk(rng: np.random.Generator, priority: str) -> tuple[int, int]:
    likelihood = int(rng.choice(range(1, 6), p=LIKELIHOOD_WEIGHTS[priority]))
    consequence = int(rng.choice(range(1, 6), p=CONSEQUENCE_WEIGHTS[priority]))
    return likelihood, consequence


def _generated_name(
    rng: np.random.Generator, base: str, domain: str, used: set[str]
) -> str:
    asset = str(rng.choice(ASSET_TEMPLATES[domain]))
    name = f"{base} {asset}"
    stage = 2
    while name in used:
        name = f"{base} {asset} — Stage {stage}"
        stage += 1
    return name


def build_projects(rng: np.random.Generator) -> pd.DataFrame:
    priorities = [p for p, n in PRIORITY_COUNTS.items() for _ in range(n)]
    for _, _, _, named_priority, _ in NAMED_PROJECTS:
        priorities.remove(named_priority)
    rng.shuffle(priorities)

    rows: list[ProjectRow] = []
    used_names: set[str] = set()
    for name, base, domain, priority, budget_m in NAMED_PROJECTS:
        start, end = _schedule(rng, budget_m)
        spi, cpi = _performance(rng, priority)
        likelihood, consequence = _risk(rng, priority)
        used_names.add(name)
        rows.append(ProjectRow(
            f"HI-{len(rows) + 1:03d}", name, base, domain, priority,
            budget_m, start, end, spi, cpi, likelihood, consequence,
        ))

    for priority in priorities:
        base = str(rng.choice(BASES))
        domain = str(rng.choice(DOMAINS))
        name = _generated_name(rng, base, domain, used_names)
        used_names.add(name)
        budget_m = _budget(rng, priority)
        start, end = _schedule(rng, budget_m)
        spi, cpi = _performance(rng, priority)
        likelihood, consequence = _risk(rng, priority)
        rows.append(ProjectRow(
            f"HI-{len(rows) + 1:03d}", name, base, domain, priority,
            round(budget_m, 2), start, end, spi, cpi, likelihood, consequence,
        ))

    frame = pd.DataFrame([vars(r) for r in rows])
    frame["risk_score"] = frame["likelihood"] * frame["consequence"]
    frame["pct_complete"] = [
        round(_pct_complete(s, e, spi, AS_AT_DATE), 1)
        for s, e, spi in zip(frame["start_date"], frame["end_date"], frame["spi"])
    ]
    frame["rag_status"] = [
        _rag_status(spi, cpi, end, AS_AT_DATE)
        for spi, cpi, end in zip(frame["spi"], frame["cpi"], frame["end_date"])
    ]
    frame["spi"] = frame["spi"].round(3)
    frame["cpi"] = frame["cpi"].round(3)
    return frame


def build_financials(projects: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in projects.itertuples():
        months = pd.date_range(row.start_date, row.end_date, freq="ME")
        if len(months) == 0:
            continue
        x = np.linspace(0.0, np.pi, len(months))
        weights = (np.sin(x) + 0.25) * rng.uniform(0.85, 1.15, len(months))
        planned = weights / weights.sum() * row.budget_m
        for month, plan_m in zip(months, planned):
            is_actual = month.date() <= AS_AT_DATE
            earned = plan_m * row.spi * rng.uniform(0.96, 1.04) if is_actual else None
            actual = earned / row.cpi * rng.uniform(0.98, 1.02) if is_actual else None
            rows.append({
                "project_id": row.project_id,
                "month_end": month.date(),
                "planned_m": round(float(plan_m), 4),
                "earned_m": round(float(earned), 4) if earned is not None else None,
                "actual_m": round(float(actual), 4) if actual is not None else None,
            })
    return pd.DataFrame(rows)


def main() -> None:
    rng = np.random.default_rng(SEED)
    DATA_DIR.mkdir(exist_ok=True)
    CSV_DIR.mkdir(exist_ok=True)

    projects = build_projects(rng)
    financials = build_financials(projects, rng)
    assert len(projects) == TOTAL_PROJECTS, len(projects)

    con = duckdb.connect(str(DB_PATH))
    try:
        for name, frame in (("projects", projects), ("financials", financials)):
            con.register(f"df_{name}", frame)
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM df_{name}")
            frame.to_csv(CSV_DIR / f"{name}.csv", index=False)
    finally:
        con.close()

    by_priority = projects["priority"].value_counts().to_dict()
    print(f"Wrote {DB_PATH}")
    print(f"  projects={len(projects)} financial rows={len(financials)}")
    print(f"  priorities={by_priority} (Medium+Low="
          f"{by_priority['Medium'] + by_priority['Low']})")
    print(f"  total budget ${projects['budget_m'].sum():,.1f}M | "
          f"named projects present: "
          f"{projects['name'].isin([n for n, *_ in NAMED_PROJECTS]).sum()}/4")


if __name__ == "__main__":
    main()

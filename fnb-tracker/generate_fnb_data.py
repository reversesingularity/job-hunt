"""Generate seeded mock delivery data for the FNB Tranche 1a portfolio.

Writes a DuckDB database (data/fnb.duckdb) with four tables - projects,
phases, financials, milestones - plus CSV exports of each. All figures are
synthetic; only the budget envelopes and project names reflect published
Budget 25 / DEPP 2025 parameters.

Usage: python generate_fnb_data.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import duckdb
import numpy as np
import pandas as pd
from config import (
    AS_AT_DATE,
    CSV_DIR,
    DATA_DIR,
    DB_PATH,
    PROGRAMME_END,
    PROGRAMME_START,
    RAG_AMBER_FLOOR,
    RAG_GREEN_FLOOR,
    T1B_GATE_DATE,
    T1B_GATE_LABEL,
)

SEED = 42
DEFAULT_PHASES = (
    "Concept Design",
    "Preliminary Design",
    "Developed Design",
    "Detailed Design",
    "Enabling Works",
)


@dataclass(frozen=True)
class ProjectSpec:
    """Static definition of one Tranche 1a project."""

    project_id: str
    short_name: str
    name: str
    description: str
    capital_m: float
    operating_m: float
    start_offset_months: int
    phase_names: tuple[str, ...]
    phase_durations: tuple[int, ...]  # months per phase
    spi: float  # schedule performance factor baked into actuals
    cpi: float  # cost performance factor baked into actuals


PROJECT_SPECS: tuple[ProjectSpec, ...] = (
    ProjectSpec(
        "P-01", "OTS Narrow Neck", "New Officer Training School Facility",
        "New officer training school facility at Narrow Neck supporting RNZN "
        "initial officer training throughput.",
        6.200, 0.900, 0, DEFAULT_PHASES, (4, 6, 7, 8, 10), 1.02, 1.00,
    ),
    ProjectSpec(
        "P-02", "SSTS Facility", "Replacement Sea Safety Training Squadron Facility",
        "Replacement sea safety training squadron facility including wet "
        "training environments and simulation spaces.",
        4.100, 0.700, 2, DEFAULT_PHASES, (4, 6, 6, 8, 9), 0.97, 1.01,
    ),
    ProjectSpec(
        "P-03", "Caisson Gates", "Replacement of Dry Dock Caisson Gates",
        "Replacement of the Calliope dry dock caisson gates - specialist "
        "marine engineering design with long-lead survey and fabrication inputs.",
        5.800, 1.100, 1, DEFAULT_PHASES, (5, 7, 8, 9, 10), 0.82, 0.91,
    ),
    ProjectSpec(
        "P-04", "Stanley Bay Gate", "Redevelopment of Stanley Bay Gate Entrance",
        "Redevelopment of the Stanley Bay Gate entrance - access control, "
        "traffic management and heritage consenting interfaces.",
        2.900, 0.550, 3, DEFAULT_PHASES, (3, 5, 6, 7, 8), 0.92, 0.96,
    ),
    ProjectSpec(
        "P-05", "Temp Offices", "Temporary Multi-Purpose Office Spaces",
        "Temporary multi-purpose office spaces enabling decant of base "
        "personnel ahead of Tranche 1b construction.",
        3.485, 1.275, 0, DEFAULT_PHASES, (2, 3, 4, 5, 12), 1.00, 1.06,
    ),
    ProjectSpec(
        "P-06", "Horizontal Infra", "Base-Wide Horizontal Infrastructure Network Planning",
        "Base-wide horizontal infrastructure network planning - power, water, "
        "wastewater, comms and wharf services feeding the Tranche 1b DBC.",
        2.700, 0.850, 0,
        ("Network Baseline Survey", "Options Assessment", "Utilities Master Plan",
         "Integration Design", "T1b DBC Inputs"),
        (6, 8, 9, 10, 5), 0.95, 0.98,
    ),
)


def _add_months(start: date, months: int) -> date:
    """Return the first day of the month `months` after `start`."""
    total = start.year * 12 + (start.month - 1) + months
    return date(total // 12, total % 12 + 1, 1)


def _rag_status(spi: float, cpi: float) -> str:
    worst = min(spi, cpi)
    if worst >= RAG_GREEN_FLOOR:
        return "On Track"
    if worst >= RAG_AMBER_FLOOR:
        return "At Risk"
    return "Behind"


def _phase_status(start: date, end: date, project_rag: str, as_at: date) -> str:
    if end <= as_at:
        return "Complete"
    if start > as_at:
        return "Planned"
    return project_rag


def _phase_pct_complete(start: date, end: date, spi: float, as_at: date) -> float:
    if end <= as_at:
        return 100.0
    if start > as_at:
        return 0.0
    elapsed = (as_at - start).days / max((end - start).days, 1)
    return float(np.clip(elapsed * spi * 100.0, 5.0, 95.0))


def build_phases(spec: ProjectSpec, as_at: date) -> pd.DataFrame:
    """Expand a project spec into dated phase rows."""
    rag = _rag_status(spec.spi, spec.cpi)
    rows: list[dict[str, object]] = []
    cursor = _add_months(PROGRAMME_START, spec.start_offset_months)
    for order, (phase, months) in enumerate(
        zip(spec.phase_names, spec.phase_durations), start=1
    ):
        end = _add_months(cursor, months)
        rows.append({
            "project_id": spec.project_id,
            "phase": phase,
            "phase_order": order,
            "start_date": cursor,
            "end_date": end,
            "status": _phase_status(cursor, end, rag, as_at),
            "pct_complete": round(_phase_pct_complete(cursor, end, spec.spi, as_at), 1),
        })
        cursor = end
    return pd.DataFrame(rows)


def _monthly_weights(rng: np.random.Generator, n_active: int, bell: bool) -> np.ndarray:
    """Spend profile across a project's active months (sums to 1)."""
    x = np.linspace(0.0, np.pi, n_active)
    base = np.sin(x) + 0.25 if bell else np.ones(n_active)
    noisy = base * rng.uniform(0.85, 1.15, n_active)
    return noisy / noisy.sum()


def build_financials(
    spec: ProjectSpec, phases: pd.DataFrame, rng: np.random.Generator, as_at: date
) -> pd.DataFrame:
    """Monthly PV / EV / AC ledger rows for one project, split by expense type."""
    months = pd.date_range(PROGRAMME_START, PROGRAMME_END, freq="ME")
    p_start = phases["start_date"].min()
    p_end = phases["end_date"].max()
    active = [m for m in months if p_start <= m.date() <= p_end]
    rows: list[dict[str, object]] = []
    for expense_type, budget, bell in (
        ("Capital", spec.capital_m, True),
        ("Operating", spec.operating_m, False),
    ):
        planned = _monthly_weights(rng, len(active), bell) * budget
        for month, plan_m in zip(active, planned):
            is_actual = month.date() <= as_at
            earned = plan_m * spec.spi * rng.uniform(0.95, 1.05) if is_actual else None
            actual = earned / spec.cpi * rng.uniform(0.97, 1.03) if is_actual else None
            rows.append({
                "project_id": spec.project_id,
                "month_end": month.date(),
                "expense_type": expense_type,
                "planned_m": round(float(plan_m), 4),
                "earned_m": round(float(earned), 4) if earned is not None else None,
                "actual_m": round(float(actual), 4) if actual is not None else None,
            })
    return pd.DataFrame(rows)


def build_milestones(spec: ProjectSpec, phases: pd.DataFrame, as_at: date) -> pd.DataFrame:
    """Key stage gates per project: concept close, developed design close, RFT ready."""
    rag = _rag_status(spec.spi, spec.cpi)
    picks = {1: "complete", 3: "complete", 5: "RFT Ready"}
    rows: list[dict[str, object]] = []
    for order, label in picks.items():
        phase_row = phases.loc[phases["phase_order"] == order].iloc[0]
        due: date = phase_row["end_date"]
        name = (
            f"{phase_row['phase']} Complete" if label == "complete"
            else "Ready for Tender (RFT)"
        )
        rows.append({
            "project_id": spec.project_id,
            "milestone": name,
            "due_date": due,
            "milestone_type": "stage_gate",
            "status": "Complete" if due <= as_at else rag,
        })
    return pd.DataFrame(rows)


def programme_milestones() -> pd.DataFrame:
    """Programme-level gates that sit above individual projects."""
    return pd.DataFrame([
        {
            "project_id": None,
            "milestone": "Tranche 1a Funding Approved (Budget 25)",
            "due_date": date(2025, 5, 22),
            "milestone_type": "programme_gate",
            "status": "Complete",
        },
        {
            "project_id": None,
            "milestone": T1B_GATE_LABEL,
            "due_date": T1B_GATE_DATE,
            "milestone_type": "programme_gate",
            "status": "On Track",
        },
    ])


def build_projects(specs: tuple[ProjectSpec, ...]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "project_id": s.project_id,
            "short_name": s.short_name,
            "name": s.name,
            "description": s.description,
            "capital_budget_m": s.capital_m,
            "operating_budget_m": s.operating_m,
            "spi": s.spi,
            "cpi": s.cpi,
            "rag_status": _rag_status(s.spi, s.cpi),
        }
        for s in specs
    ])


def main() -> None:
    rng = np.random.default_rng(SEED)
    DATA_DIR.mkdir(exist_ok=True)
    CSV_DIR.mkdir(exist_ok=True)

    projects = build_projects(PROJECT_SPECS)
    phase_frames = {s.project_id: build_phases(s, AS_AT_DATE) for s in PROJECT_SPECS}
    phases = pd.concat(phase_frames.values(), ignore_index=True)
    financials = pd.concat(
        [build_financials(s, phase_frames[s.project_id], rng, AS_AT_DATE)
         for s in PROJECT_SPECS],
        ignore_index=True,
    )
    milestones = pd.concat(
        [build_milestones(s, phase_frames[s.project_id], AS_AT_DATE)
         for s in PROJECT_SPECS] + [programme_milestones()],
        ignore_index=True,
    )

    tables = {
        "projects": projects,
        "phases": phases,
        "financials": financials,
        "milestones": milestones,
    }
    con = duckdb.connect(str(DB_PATH))
    try:
        for name, frame in tables.items():
            con.register(f"df_{name}", frame)
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM df_{name}")
            frame.to_csv(CSV_DIR / f"{name}.csv", index=False)
    finally:
        con.close()

    cap = financials.loc[financials["expense_type"] == "Capital", "planned_m"].sum()
    opx = financials.loc[financials["expense_type"] == "Operating", "planned_m"].sum()
    print(f"Wrote {DB_PATH}")
    print(f"  projects={len(projects)} phases={len(phases)} "
          f"financials={len(financials)} milestones={len(milestones)}")
    print(f"  planned capital ${cap:.3f}M (envelope $25.185M) | "
          f"planned operating ${opx:.3f}M (envelope $5.375M)")


if __name__ == "__main__":
    main()

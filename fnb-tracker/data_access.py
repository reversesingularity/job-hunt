"""DuckDB query layer for the FNB Tranche 1 Delivery Tracker.

Base tables are loaded once per session via st.cache_data; interactive
filtering happens in pandas on the cached frames.
"""

from __future__ import annotations

from datetime import date

import duckdb
import pandas as pd
import streamlit as st
from config import DB_PATH


def _query(sql: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return con.execute(sql).df()
    finally:
        con.close()


@st.cache_data(show_spinner=False)
def load_projects() -> pd.DataFrame:
    return _query("SELECT * FROM projects ORDER BY project_id")


@st.cache_data(show_spinner=False)
def load_phases() -> pd.DataFrame:
    return _query("SELECT * FROM phases ORDER BY project_id, phase_order")


@st.cache_data(show_spinner=False)
def load_financials() -> pd.DataFrame:
    return _query(
        """
        SELECT project_id, CAST(month_end AS DATE) AS month_end,
               expense_type, planned_m, earned_m, actual_m
        FROM financials
        ORDER BY project_id, expense_type, month_end
        """
    )


@st.cache_data(show_spinner=False)
def load_milestones() -> pd.DataFrame:
    return _query(
        "SELECT * FROM milestones ORDER BY due_date, project_id NULLS FIRST"
    )


def financial_slice(
    financials: pd.DataFrame,
    project_ids: list[str],
    expense_types: list[str],
    as_at: date,
) -> pd.DataFrame:
    """Filtered copy of the ledger; actuals masked after the as-at date."""
    mask = (
        financials["project_id"].isin(project_ids)
        & financials["expense_type"].isin(expense_types)
    )
    sliced = financials.loc[mask].copy()
    future = sliced["month_end"] > pd.Timestamp(as_at)
    sliced.loc[future, ["earned_m", "actual_m"]] = pd.NA
    return sliced


def monthly_rollup(fin_slice: pd.DataFrame) -> pd.DataFrame:
    """Programme-level monthly PV/EV/AC with cumulative columns."""
    rolled = (
        fin_slice.groupby("month_end", as_index=False)[
            ["planned_m", "earned_m", "actual_m"]
        ]
        .sum(min_count=1)
        .sort_values("month_end")
    )
    for col in ("planned_m", "earned_m", "actual_m"):
        rolled[f"cum_{col}"] = rolled[col].cumsum()
    return rolled


def evm_summary(fin_slice: pd.DataFrame, as_at: date) -> dict[str, float]:
    """Spend to date plus SPI (EV/PV) and CPI (EV/AC) as at the report date."""
    to_date = fin_slice.loc[fin_slice["month_end"] <= pd.Timestamp(as_at)]
    pv = float(to_date["planned_m"].sum())
    ev = float(to_date["earned_m"].sum())
    ac = float(to_date["actual_m"].sum())
    return {
        "planned_to_date": pv,
        "earned_to_date": ev,
        "actual_to_date": ac,
        "spi": ev / pv if pv else 0.0,
        "cpi": ev / ac if ac else 0.0,
    }


def current_phase(phases: pd.DataFrame, project_id: str) -> str:
    """Name of the earliest in-flight phase (falls back to next planned/last)."""
    rows = phases.loc[phases["project_id"] == project_id].sort_values("phase_order")
    active = rows.loc[rows["status"].isin(("On Track", "At Risk", "Behind"))]
    if not active.empty:
        return str(active.iloc[0]["phase"])
    planned = rows.loc[rows["status"] == "Planned"]
    if not planned.empty:
        return str(planned.iloc[0]["phase"])
    return str(rows.iloc[-1]["phase"])


def project_evm_table(
    fin_slice: pd.DataFrame, projects: pd.DataFrame, as_at: date
) -> pd.DataFrame:
    """Per-project SPI/CPI/spend derived from the filtered ledger."""
    to_date = fin_slice.loc[fin_slice["month_end"] <= pd.Timestamp(as_at)]
    agg = to_date.groupby("project_id", as_index=False)[
        ["planned_m", "earned_m", "actual_m"]
    ].sum(min_count=1)
    agg["spi"] = agg["earned_m"] / agg["planned_m"]
    agg["cpi"] = agg["earned_m"] / agg["actual_m"]
    return projects.merge(
        agg[["project_id", "planned_m", "actual_m", "spi", "cpi"]],
        on="project_id",
        how="inner",
        suffixes=("_baseline", ""),
    )

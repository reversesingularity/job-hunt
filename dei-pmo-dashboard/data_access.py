"""DuckDB query layer for the DE&I Horizontal Infrastructure PMO Dashboard."""

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
    return _query(
        """
        SELECT project_id, name, base, domain, priority, budget_m,
               CAST(start_date AS DATE) AS start_date,
               CAST(end_date AS DATE) AS end_date,
               spi, cpi, likelihood, consequence, risk_score,
               pct_complete, rag_status
        FROM projects
        ORDER BY project_id
        """
    )


@st.cache_data(show_spinner=False)
def load_financials() -> pd.DataFrame:
    return _query(
        """
        SELECT project_id, CAST(month_end AS DATE) AS month_end,
               planned_m, earned_m, actual_m
        FROM financials
        ORDER BY project_id, month_end
        """
    )


def filter_projects(
    projects: pd.DataFrame, bases: list[str], priorities: list[str]
) -> pd.DataFrame:
    mask = projects["base"].isin(bases) & projects["priority"].isin(priorities)
    return projects.loc[mask].copy()


def financial_slice(
    financials: pd.DataFrame, project_ids: list[str], as_at: date
) -> pd.DataFrame:
    """Filtered ledger copy; actuals masked after the as-at date."""
    sliced = financials.loc[financials["project_id"].isin(project_ids)].copy()
    future = sliced["month_end"] > pd.Timestamp(as_at)
    sliced.loc[future, ["earned_m", "actual_m"]] = pd.NA
    return sliced


def monthly_rollup(fin_slice: pd.DataFrame) -> pd.DataFrame:
    """Monthly PV/EV/AC across the slice with cumulative columns."""
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


def top_n_by_budget(projects: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return projects.nlargest(n, "budget_m").copy()

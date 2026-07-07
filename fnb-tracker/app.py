"""FNB Tranche 1 Delivery Tracker - Streamlit entry point.

Run with: streamlit run app.py
Regenerate mock data first if needed: python generate_fnb_data.py
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st
from config import AS_AT_DATE, DB_PATH, INK_MUTED
from data_access import (
    financial_slice,
    load_financials,
    load_milestones,
    load_phases,
    load_projects,
)
from views import deep_dive, gantt, kpi

st.set_page_config(
    page_title="FNB Tranche 1 Delivery Tracker",
    page_icon="⚓",
    layout="wide",
)


def _sidebar(projects: pd.DataFrame, financials: pd.DataFrame) -> tuple[list[str], list[str], date]:
    """Render filters; return (project_ids, expense_types, as_at date)."""
    st.sidebar.title("⚓ FNB Tranche 1")
    st.sidebar.markdown(
        "**Devonport Naval Base Regeneration**  \n"
        "Tranche 1a — Design & Enabling Works  \n"
        f"<span style='color:{INK_MUTED};'>Capital \\$25.185M · Operating "
        "\\$5.375M · FY26–FY29</span>",
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    names = st.sidebar.multiselect(
        "Projects", projects["short_name"].tolist(),
        default=projects["short_name"].tolist(),
    )
    ids = projects.loc[projects["short_name"].isin(names), "project_id"].tolist()

    expense = st.sidebar.radio(
        "Expense type", ("All", "Capital", "Operating"), horizontal=True
    )
    expense_types = ["Capital", "Operating"] if expense == "All" else [expense]

    report_months = sorted(
        m.date() for m in financials["month_end"].unique()
        if m.date() <= AS_AT_DATE and m.date() >= date(2025, 9, 30)
    )
    as_at = st.sidebar.select_slider(
        "Reporting month (as at)", options=report_months,
        value=report_months[-1], format_func=lambda d: f"{d:%b %Y}",
    )

    st.sidebar.divider()
    st.sidebar.caption(
        "Portfolio demonstration piece. Budget envelopes and project scope "
        "reflect Budget 25 / Defence Estate Portfolio Plan 2025 (Tranche 1a); "
        "all schedule and cost data are synthetic."
    )
    return ids, expense_types, as_at


def main() -> None:
    if not DB_PATH.exists():
        st.error(
            "Database not found. Run `python generate_fnb_data.py` first to "
            "generate the mock dataset."
        )
        st.stop()

    projects = load_projects()
    phases = load_phases()
    financials = load_financials()
    milestones = load_milestones()

    ids, expense_types, as_at = _sidebar(projects, financials)
    if not ids:
        st.warning("Select at least one project in the sidebar.")
        st.stop()

    selected = projects.loc[projects["project_id"].isin(ids)]
    fin_slice = financial_slice(financials, ids, expense_types, as_at)

    st.title("Future Naval Base — Tranche 1 Delivery Tracker")
    st.caption(
        f"Design & enabling works portfolio · reporting as at {as_at:%d %B %Y} "
        "· on time, on budget, in full"
    )

    tab_summary, tab_schedule, tab_projects = st.tabs(
        ("Executive Summary", "Schedule & Gates", "Project Deep Dive")
    )
    with tab_summary:
        kpi.render(selected, phases, financials, fin_slice, expense_types, as_at)
    with tab_schedule:
        gantt.render(selected, phases, milestones, as_at)
    with tab_projects:
        deep_dive.render(selected, phases, financials, milestones, as_at)


if __name__ == "__main__":
    main()

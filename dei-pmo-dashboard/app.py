"""DE&I Horizontal Infrastructure PMO Dashboard — Streamlit entry point.

Run with: streamlit run app.py
Regenerate mock data first if needed: python generate_mock_data.py
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from config import (
    AS_AT_DATE,
    BASES,
    DB_PATH,
    INK_MUTED,
    PRIORITY_ORDER,
    TOTAL_PROJECTS,
)
from data_access import (
    filter_projects,
    financial_slice,
    load_financials,
    load_projects,
)
from views import financial, overview, risk

st.set_page_config(
    page_title="DE&I Horizontal Infrastructure PMO",
    page_icon="🏗️",
    layout="wide",
)


def _sidebar(projects: pd.DataFrame, financials: pd.DataFrame) -> tuple[list[str], list[str], date]:
    """Render filters; return (bases, priorities, as_at date)."""
    st.sidebar.title("🏗️ DE&I PMO")
    st.sidebar.markdown(
        "**Defence Estate & Infrastructure**  \n"
        "Horizontal infrastructure portfolio  \n"
        f"<span style='color:{INK_MUTED};'>{TOTAL_PROJECTS} projects · "
        "24 Critical / 45 High / 72 Medium-Low</span>",
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    bases = st.sidebar.multiselect(
        "Base locations",
        list(BASES),
        default=list(BASES),
    )
    priorities = st.sidebar.multiselect(
        "Priority",
        list(PRIORITY_ORDER),
        default=list(PRIORITY_ORDER),
    )

    report_months = sorted(
        m.date()
        for m in financials["month_end"].unique()
        if m.date() <= AS_AT_DATE
    )
    as_at = st.sidebar.select_slider(
        "Reporting month (as at)",
        options=report_months,
        value=report_months[-1],
        format_func=lambda d: f"{d:%b %Y}",
    )

    st.sidebar.divider()
    st.sidebar.caption(
        "Sourced from publicly available Official Information Act (OIA) "
        "release OIA-2025-5483. © Crown Copyright."
    )
    st.sidebar.caption(
        "Portfolio demonstration piece. Project counts and priority split "
        "reflect the 2025 Defence Estate Portfolio Plan; all schedule, cost, "
        "and risk figures are synthetic."
    )
    return bases, priorities, as_at


def main() -> None:
    if not DB_PATH.exists():
        st.error(
            "Database not found. Run `python generate_mock_data.py` first to "
            "generate the mock dataset."
        )
        st.stop()

    projects = load_projects()
    financials = load_financials()

    bases, priorities, as_at = _sidebar(projects, financials)
    if not bases or not priorities:
        st.warning("Select at least one base and one priority in the sidebar.")
        st.stop()

    selected = filter_projects(projects, bases, priorities)
    if selected.empty:
        st.warning("No projects match the current filters.")
        st.stop()

    fin_slice = financial_slice(financials, selected["project_id"].tolist(), as_at)

    st.title("Defence Estate & Infrastructure — Horizontal PMO Dashboard")
    st.caption(
        f"141-project portfolio · reporting as at {as_at:%d %B %Y} · "
        f"{len(selected)} of {TOTAL_PROJECTS} projects selected"
    )
    st.caption(
        "*Sourced from publicly available Official Information Act (OIA) "
        "release OIA-2025-5483. © Crown Copyright.*"
    )

    tab_overview, tab_risk, tab_financial = st.tabs(
        ("Executive Overview", "Risk Management", "Financial & Schedule")
    )
    with tab_overview:
        overview.render(selected, fin_slice, as_at)
    with tab_risk:
        risk.render(selected)
    with tab_financial:
        financial.render(selected, financials, as_at)


if __name__ == "__main__":
    main()

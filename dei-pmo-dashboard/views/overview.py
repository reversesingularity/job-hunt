"""Tab 1 - Executive Overview: portfolio KPIs, mix charts, at-risk register."""

from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import (
    INK_SECONDARY,
    PRIORITY_ORDER,
    SERIES,
    STATUS_COLOURS,
    STATUS_ICONS,
)
from data_access import evm_summary
from views.chart_theme import plan_delta, themed


def _priority_chart(projects: pd.DataFrame) -> go.Figure:
    counts = (
        projects["priority"].value_counts().reindex(PRIORITY_ORDER).fillna(0)
    )
    fig = go.Figure(go.Bar(
        x=list(counts.index), y=counts.to_numpy(),
        marker_color=SERIES["blue"],
        text=[int(v) for v in counts.to_numpy()],
        textposition="outside", textfont={"color": INK_SECONDARY},
        hovertemplate="%{x}: %{y} projects<extra></extra>",
    ))
    fig.update_layout(
        title={"text": "Projects by priority",
               "font": {"color": INK_SECONDARY, "size": 15}},
        showlegend=False,
    )
    return themed(fig, height=340)


def _base_budget_chart(projects: pd.DataFrame) -> go.Figure:
    totals = (
        projects.groupby("base")["budget_m"].sum().sort_values(ascending=True)
    )
    fig = go.Figure(go.Bar(
        x=totals.to_numpy(), y=list(totals.index), orientation="h",
        marker_color=SERIES["blue"],
        hovertemplate="%{y}: $%{x:.1f}M<extra></extra>",
    ))
    fig.update_layout(
        title={"text": "Budget by base location ($M)",
               "font": {"color": INK_SECONDARY, "size": 15}},
        showlegend=False,
        xaxis={"ticksuffix": "M"},
    )
    return themed(fig, height=340)


def _at_risk_table(projects: pd.DataFrame) -> None:
    at_risk = (
        projects.loc[projects["rag_status"].isin(("At Risk", "Behind"))]
        .nlargest(15, "budget_m")
        .assign(status_label=lambda d: d["rag_status"].map(
            lambda s: f"{STATUS_ICONS[s]} {s}"
        ))
        [["project_id", "name", "base", "priority", "spi", "cpi",
          "budget_m", "status_label"]]
    )
    if at_risk.empty:
        st.info("No projects at risk under the current filters.")
        return

    def colour_status(label: str) -> str:
        status = label.split(" ", 1)[1]
        return f"color: {STATUS_COLOURS[status]}; font-weight: 700"

    styler = (
        at_risk.rename(columns={
            "project_id": "ID", "name": "Project", "base": "Base",
            "priority": "Priority", "spi": "SPI", "cpi": "CPI",
            "budget_m": "Budget ($M)", "status_label": "Status",
        })
        .style.map(colour_status, subset=["Status"])
        .format({"SPI": "{:.2f}", "CPI": "{:.2f}", "Budget ($M)": "{:.1f}"})
    )
    st.dataframe(styler, hide_index=True, use_container_width=True)


def render(projects: pd.DataFrame, fin_slice: pd.DataFrame, as_at: date) -> None:
    evm = evm_summary(fin_slice, as_at)
    budget_total = float(projects["budget_m"].sum())
    n_at_risk = int(projects["rag_status"].isin(("At Risk", "Behind")).sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Portfolio Budget", f"${budget_total:,.0f}M",
              f"{len(projects)} projects", delta_color="off", border=True)
    c2.metric(
        "Spend to Date", f"${evm['actual_to_date']:,.0f}M",
        f"{evm['actual_to_date'] / budget_total * 100:.0f}% of budget",
        delta_color="off", border=True,
    )
    c3.metric("Portfolio SPI", f"{evm['spi']:.2f}", *plan_delta(evm["spi"]),
              border=True)
    c4.metric("Portfolio CPI", f"{evm['cpi']:.2f}", *plan_delta(evm["cpi"]),
              border=True)
    c5.metric("Projects at Risk", f"{n_at_risk}",
              f"of {len(projects)} selected", delta_color="off", border=True)

    left, right = st.columns(2)
    with left:
        st.plotly_chart(_priority_chart(projects), use_container_width=True)
    with right:
        st.plotly_chart(_base_budget_chart(projects), use_container_width=True)

    st.subheader("At-risk register — top 15 by budget")
    _at_risk_table(projects)

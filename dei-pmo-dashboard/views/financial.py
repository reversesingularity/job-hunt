"""Tab 3 - Financial & Schedule: top-10 Gantt, burndown, EVM table."""

from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import (
    INK_MUTED,
    INK_SECONDARY,
    SERIES,
    STATUS_COLOURS,
    STATUS_ICONS,
)
from data_access import financial_slice, monthly_rollup, top_n_by_budget
from views.chart_theme import themed

_STATUS_ORDER = ("Complete", "On Track", "At Risk", "Behind")


def _gantt_figure(top: pd.DataFrame, as_at: date) -> go.Figure:
    fig = px.timeline(
        top,
        x_start="start_date",
        x_end="end_date",
        y="name",
        color="rag_status",
        color_discrete_map=STATUS_COLOURS,
        category_orders={"rag_status": list(_STATUS_ORDER)},
        custom_data=["project_id", "budget_m", "pct_complete", "rag_status"],
    )
    fig.update_traces(
        marker_line_width=0,
        hovertemplate=(
            "<b>%{y}</b> (%{customdata[0]})<br>$%{customdata[1]:.1f}M · "
            "%{customdata[2]:.0f}% complete · %{customdata[3]}<extra></extra>"
        ),
    )
    fig.update_yaxes(
        autorange="reversed", categoryorder="array",
        categoryarray=top["name"].tolist(), title=None,
    )
    fig.add_shape(
        type="line", x0=as_at, x1=as_at, y0=0, y1=1, yref="paper",
        line={"color": INK_MUTED, "width": 1, "dash": "dot"},
    )
    fig.add_annotation(
        x=as_at, y=1.04, yref="paper", text=f"as at {as_at:%b %Y}",
        showarrow=False, font={"color": INK_MUTED, "size": 11},
    )
    fig.update_layout(
        title={"text": "Top 10 by budget — delivery schedule",
               "font": {"color": INK_SECONDARY, "size": 15}},
        legend_title_text="",
    )
    return themed(fig, height=440)


def _burndown_figure(
    rollup: pd.DataFrame, envelope: float, as_at: date
) -> go.Figure:
    remaining_planned = envelope - rollup["cum_planned_m"]
    actual = rollup.dropna(subset=["cum_actual_m"])
    remaining_actual = envelope - actual["cum_actual_m"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rollup["month_end"], y=remaining_planned, name="Planned remaining",
        mode="lines", line={"color": SERIES["blue"], "width": 2},
        hovertemplate="%{y:.1f}M<extra>Planned remaining</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=actual["month_end"], y=remaining_actual, name="Actual remaining",
        mode="lines", line={"color": SERIES["aqua"], "width": 2},
        hovertemplate="%{y:.1f}M<extra>Actual remaining</extra>",
    ))
    fig.add_shape(
        type="line", x0=as_at, x1=as_at, y0=0, y1=1, yref="paper",
        line={"color": INK_MUTED, "width": 1, "dash": "dot"},
    )
    fig.update_layout(
        title={"text": "Top 10 budget burndown — envelope remaining ($M)",
               "font": {"color": INK_SECONDARY, "size": 15}},
        hovermode="x unified",
        yaxis={"ticksuffix": "M", "rangemode": "tozero"},
    )
    return themed(fig, height=380)


def _evm_table(top: pd.DataFrame, fin_slice: pd.DataFrame, as_at: date) -> None:
    spend = (
        fin_slice.loc[fin_slice["month_end"] <= pd.Timestamp(as_at)]
        .groupby("project_id", as_index=False)["actual_m"].sum(min_count=1)
        .rename(columns={"actual_m": "spend_m"})
    )
    frame = (
        top.merge(spend, on="project_id", how="left")
        .assign(status_label=lambda d: d["rag_status"].map(
            lambda s: f"{STATUS_ICONS[s]} {s}"
        ))
        [["project_id", "name", "base", "budget_m", "spend_m",
          "pct_complete", "spi", "cpi", "status_label"]]
    )

    def colour_status(label: str) -> str:
        status = label.split(" ", 1)[1]
        return f"color: {STATUS_COLOURS[status]}; font-weight: 700"

    styler = (
        frame.rename(columns={
            "project_id": "ID", "name": "Project", "base": "Base",
            "budget_m": "Budget ($M)", "spend_m": "Spend to Date ($M)",
            "pct_complete": "Complete (%)", "spi": "SPI", "cpi": "CPI",
            "status_label": "Status",
        })
        .style.map(colour_status, subset=["Status"])
        .format({"Budget ($M)": "{:.1f}", "Spend to Date ($M)": "{:.1f}",
                 "Complete (%)": "{:.0f}%", "SPI": "{:.2f}", "CPI": "{:.2f}"})
    )
    st.dataframe(styler, hide_index=True, use_container_width=True)


def render(
    projects: pd.DataFrame, financials: pd.DataFrame, as_at: date
) -> None:
    top = top_n_by_budget(projects, 10)
    if top.empty:
        st.warning("No projects match the current filters.")
        return
    fin_slice = financial_slice(financials, top["project_id"].tolist(), as_at)

    st.plotly_chart(_gantt_figure(top, as_at), use_container_width=True)
    st.plotly_chart(
        _burndown_figure(
            monthly_rollup(fin_slice), float(top["budget_m"].sum()), as_at
        ),
        use_container_width=True,
    )
    st.subheader("Top 10 EVM summary")
    _evm_table(top, fin_slice, as_at)

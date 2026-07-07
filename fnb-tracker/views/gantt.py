"""Tab 2 - Schedule & Gates: phase Gantt, stage-gate diamonds, T1b gate."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from config import (
    INK_MUTED,
    INK_PRIMARY,
    INK_SECONDARY,
    PROGRAMME_END,
    PROGRAMME_START,
    SERIES,
    STATUS_COLOURS,
    STATUS_ICONS,
    SURFACE,
    T1B_GATE_DATE,
    T1B_GATE_LABEL,
)

from views.chart_theme import themed

_STATUS_ORDER = ("Complete", "On Track", "At Risk", "Behind", "Planned")


def _gantt_figure(
    merged: pd.DataFrame, gates: pd.DataFrame, order: list[str], as_at: date
) -> go.Figure:
    fig = px.timeline(
        merged,
        x_start="start_date",
        x_end="end_date",
        y="short_name",
        color="status",
        color_discrete_map=STATUS_COLOURS,
        category_orders={"status": list(_STATUS_ORDER)},
        custom_data=["phase", "status", "pct_complete"],
    )
    fig.update_traces(
        marker_line_width=0,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>%{customdata[1]} · "
            "%{customdata[2]:.0f}% complete<extra></extra>"
        ),
    )
    fig.update_yaxes(
        autorange="reversed", categoryorder="array", categoryarray=order,
        title=None,
    )
    fig.update_xaxes(range=[PROGRAMME_START, PROGRAMME_END + timedelta(days=120)])

    fig.add_trace(go.Scatter(
        x=gates["due_date"], y=gates["short_name"], name="Stage gate",
        mode="markers",
        marker={"symbol": "diamond", "size": 11, "color": INK_PRIMARY,
                "line": {"color": SURFACE, "width": 1}},
        customdata=gates[["milestone", "status"]],
        hovertemplate="<b>%{customdata[0]}</b><br>%{x|%b %Y} · "
                      "%{customdata[1]}<extra>Stage gate</extra>",
    ))

    fig.add_shape(
        type="line", x0=as_at, x1=as_at, y0=0, y1=1, yref="paper",
        line={"color": INK_MUTED, "width": 1, "dash": "dot"},
    )
    fig.add_annotation(
        x=as_at, y=1.04, yref="paper", text=f"as at {as_at:%b %Y}",
        showarrow=False, font={"color": INK_MUTED, "size": 11},
    )
    fig.add_shape(
        type="line", x0=T1B_GATE_DATE, x1=T1B_GATE_DATE, y0=0, y1=1,
        yref="paper", line={"color": SERIES["blue"], "width": 2},
    )
    fig.add_annotation(
        x=T1B_GATE_DATE, y=0.5, yref="paper", text=f"◈ {T1B_GATE_LABEL}",
        showarrow=False, font={"color": SERIES["blue"], "size": 12},
        xanchor="left", xshift=8, textangle=90,
    )
    fig.update_layout(
        title={"text": "Design & enabling works schedule (FY26–FY29)",
               "font": {"color": INK_SECONDARY, "size": 15}},
        legend_title_text="",
    )
    return themed(fig, height=480, margin={"l": 10, "r": 10, "t": 84, "b": 10})


def _programme_gates_table(milestones: pd.DataFrame) -> None:
    gates = milestones.loc[milestones["milestone_type"] == "programme_gate"].copy()
    gates["Status"] = gates["status"].map(lambda s: f"{STATUS_ICONS[s]} {s}")
    gates["Due"] = pd.to_datetime(gates["due_date"]).dt.strftime("%b %Y")
    styler = (
        gates[["milestone", "Due", "Status"]]
        .rename(columns={"milestone": "Programme gate"})
        .style.map(
            lambda label: (
                f"color: {STATUS_COLOURS[label.split(' ', 1)[1]]}; font-weight: 700"
            ),
            subset=["Status"],
        )
    )
    st.dataframe(styler, hide_index=True, use_container_width=True)


def render(
    projects: pd.DataFrame,
    phases: pd.DataFrame,
    milestones: pd.DataFrame,
    as_at: date,
) -> None:
    merged = phases.merge(
        projects[["project_id", "short_name"]], on="project_id", how="inner"
    )
    gates = (
        milestones.loc[milestones["milestone_type"] == "stage_gate"]
        .merge(projects[["project_id", "short_name"]], on="project_id", how="inner")
    )
    order = projects.sort_values("project_id")["short_name"].tolist()

    st.plotly_chart(
        _gantt_figure(merged, gates, order, as_at), use_container_width=True
    )
    st.caption(
        "Bars are design/enabling phases coloured by delivery status; ◇ diamonds "
        "are stage gates. The solid blue line is the Tranche 1b construction "
        "funding gate (detailed business case, FY2028/29) every project must hit."
    )

    st.subheader("Programme gates")
    _programme_gates_table(milestones)

"""Tab 3 - Project Deep Dive: per-project EVM S-curve, phases, milestones."""

from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from config import (
    INK_MUTED,
    INK_SECONDARY,
    SERIES,
    STATUS_COLOURS,
    STATUS_ICONS,
)
from data_access import current_phase, evm_summary, financial_slice, monthly_rollup

from views.chart_theme import plan_delta, themed


def _s_curve(rollup: pd.DataFrame, as_at: date) -> go.Figure:
    fig = go.Figure()
    traces = (
        ("cum_planned_m", "Planned value (PV)", SERIES["blue"]),
        ("cum_earned_m", "Earned value (EV)", SERIES["aqua"]),
        ("cum_actual_m", "Actual cost (AC)", SERIES["amber"]),
    )
    for column, name, colour in traces:
        series = rollup.dropna(subset=[column])
        fig.add_trace(go.Scatter(
            x=series["month_end"], y=series[column], name=name,
            mode="lines", line={"color": colour, "width": 2},
            hovertemplate="%{y:.2f}M<extra>" + name + "</extra>",
        ))
    fig.add_shape(
        type="line", x0=as_at, x1=as_at, y0=0, y1=1, yref="paper",
        line={"color": INK_MUTED, "width": 1, "dash": "dot"},
    )
    fig.update_layout(
        title={"text": "EVM S-curve — cumulative $M",
               "font": {"color": INK_SECONDARY, "size": 15}},
        hovermode="x unified",
        yaxis={"ticksuffix": "M", "rangemode": "tozero"},
    )
    return themed(fig, height=380)


def _phase_progress(project_phases: pd.DataFrame) -> None:
    for row in project_phases.sort_values("phase_order").itertuples():
        icon = STATUS_ICONS[str(row.status)]
        st.progress(
            float(row.pct_complete) / 100.0,
            text=f"{icon} {row.phase} — {row.pct_complete:.0f}% ({row.status})",
        )


def _milestone_table(project_milestones: pd.DataFrame) -> None:
    frame = project_milestones.copy()
    frame["Status"] = frame["status"].map(lambda s: f"{STATUS_ICONS[s]} {s}")
    frame["Due"] = pd.to_datetime(frame["due_date"]).dt.strftime("%b %Y")
    styler = (
        frame[["milestone", "Due", "Status"]]
        .rename(columns={"milestone": "Milestone"})
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
    financials: pd.DataFrame,
    milestones: pd.DataFrame,
    as_at: date,
) -> None:
    name = st.selectbox("Project", projects["name"].tolist())
    project = projects.loc[projects["name"] == name].iloc[0]
    pid = str(project["project_id"])
    rag = str(project["rag_status"])

    st.caption(f"{pid} · {project['description']}")
    st.markdown(
        f"<span style='color:{STATUS_COLOURS[rag]};font-weight:700;'>"
        f"{STATUS_ICONS[rag]} {rag}</span>"
        f"<span style='color:{INK_SECONDARY};'> · Current phase: "
        f"{current_phase(phases, pid)}</span>",
        unsafe_allow_html=True,
    )

    budget = float(project["capital_budget_m"] + project["operating_budget_m"])
    fin = financial_slice(financials, [pid], ["Capital", "Operating"], as_at)
    evm = evm_summary(fin, as_at)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Total Budget", f"${budget:.3f}M",
        f"${project['capital_budget_m']:.3f}M cap · "
        f"${project['operating_budget_m']:.3f}M opx",
        delta_color="off", border=True,
    )
    c2.metric(
        "Spend to Date", f"${evm['actual_to_date']:.2f}M",
        f"{evm['actual_to_date'] / budget * 100:.0f}% consumed",
        delta_color="off", border=True,
    )
    c3.metric("SPI", f"{evm['spi']:.2f}", *plan_delta(evm["spi"]), border=True)
    c4.metric("CPI", f"{evm['cpi']:.2f}", *plan_delta(evm["cpi"]), border=True)

    left, right = st.columns([2, 3])
    with left:
        st.subheader("Phase progress")
        _phase_progress(phases.loc[phases["project_id"] == pid])
    with right:
        st.plotly_chart(_s_curve(monthly_rollup(fin), as_at), use_container_width=True)

    st.subheader("Stage gates")
    _milestone_table(milestones.loc[milestones["project_id"] == pid])

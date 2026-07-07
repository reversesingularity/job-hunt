"""Tab 1 - Executive Summary: EVM KPIs, programme health, budget burndown."""

from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from config import (
    INK_MUTED,
    INK_SECONDARY,
    RAG_AMBER_FLOOR,
    RAG_GREEN_FLOOR,
    SERIES,
    STATUS_COLOURS,
    STATUS_ICONS,
    SURFACE_CARD,
)
from data_access import (
    current_phase,
    evm_summary,
    financial_slice,
    monthly_rollup,
    project_evm_table,
)

from views.chart_theme import plan_delta, themed


def _programme_rag(spi: float, cpi: float) -> str:
    worst = min(spi, cpi)
    if worst >= RAG_GREEN_FLOOR:
        return "On Track"
    if worst >= RAG_AMBER_FLOOR:
        return "At Risk"
    return "Behind"


def _health_banner(rag: str, spi: float, cpi: float, as_at: date) -> None:
    colour = STATUS_COLOURS[rag]
    icon = STATUS_ICONS[rag]
    st.markdown(
        f"""
        <div style="background:{SURFACE_CARD};border-left:4px solid {colour};
                    border-radius:6px;padding:0.65rem 1rem;margin:0.25rem 0 1rem 0;">
          <span style="color:{colour};font-weight:700;">{icon} PROGRAMME HEALTH:
          {rag.upper()}</span>
          <span style="color:{INK_SECONDARY};"> — SPI {spi:.2f} · CPI {cpi:.2f}
          · as at {as_at:%d %b %Y}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _burndown_chart(
    rollup: pd.DataFrame, envelope: float, as_at: date
) -> go.Figure:
    remaining_planned = envelope - rollup["cum_planned_m"]
    actual = rollup.dropna(subset=["cum_actual_m"])
    remaining_actual = envelope - actual["cum_actual_m"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rollup["month_end"], y=remaining_planned, name="Planned remaining",
        mode="lines", line={"color": SERIES["blue"], "width": 2},
        hovertemplate="%{y:.2f}M<extra>Planned remaining</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=actual["month_end"], y=remaining_actual, name="Actual remaining",
        mode="lines", line={"color": SERIES["aqua"], "width": 2},
        hovertemplate="%{y:.2f}M<extra>Actual remaining</extra>",
    ))
    fig.add_shape(
        type="line", x0=as_at, x1=as_at, y0=0, y1=1, yref="paper",
        line={"color": INK_MUTED, "width": 1, "dash": "dot"},
    )
    fig.add_annotation(
        x=as_at, y=1.05, yref="paper", text=f"as at {as_at:%b %Y}",
        showarrow=False, font={"color": INK_MUTED, "size": 11},
    )
    fig.update_layout(
        title={"text": "Budget burndown — envelope remaining ($M)",
               "font": {"color": INK_SECONDARY, "size": 15}},
        hovermode="x unified",
        yaxis={"ticksuffix": "M", "rangemode": "tozero"},
    )
    return themed(fig)


def _health_table(evm_by_project: pd.DataFrame, phases: pd.DataFrame) -> None:
    frame = evm_by_project.assign(
        status_label=lambda d: d["rag_status"].map(
            lambda s: f"{STATUS_ICONS[s]} {s}"
        ),
        phase=lambda d: d["project_id"].map(
            lambda pid: current_phase(phases, pid)
        ),
        budget_m=lambda d: d["capital_budget_m"] + d["operating_budget_m"],
        consumed_pct=lambda d: d["actual_m"] / d["budget_m"] * 100.0,
    )[["short_name", "status_label", "phase", "spi", "cpi",
       "actual_m", "budget_m", "consumed_pct"]]

    def colour_status(label: str) -> str:
        status = label.split(" ", 1)[1]
        return f"color: {STATUS_COLOURS[status]}; font-weight: 700"

    styler = (
        frame.rename(columns={
            "short_name": "Project", "status_label": "Status",
            "phase": "Current Phase", "spi": "SPI", "cpi": "CPI",
            "actual_m": "Spend to Date ($M)", "budget_m": "Budget ($M)",
            "consumed_pct": "Consumed (%)",
        })
        .style.map(colour_status, subset=["Status"])
        .format({"SPI": "{:.2f}", "CPI": "{:.2f}",
                 "Spend to Date ($M)": "{:.2f}", "Budget ($M)": "{:.3f}",
                 "Consumed (%)": "{:.0f}%"})
    )
    st.dataframe(styler, hide_index=True, use_container_width=True)


def render(
    projects: pd.DataFrame,
    phases: pd.DataFrame,
    financials: pd.DataFrame,
    fin_slice: pd.DataFrame,
    expense_types: list[str],
    as_at: date,
) -> None:
    ids = projects["project_id"].tolist()
    evm = evm_summary(fin_slice, as_at)
    cap = evm_summary(financial_slice(financials, ids, ["Capital"], as_at), as_at)
    opx = evm_summary(financial_slice(financials, ids, ["Operating"], as_at), as_at)
    cap_env = float(projects["capital_budget_m"].sum())
    opx_env = float(projects["operating_budget_m"].sum())
    on_track = int((projects["rag_status"] == "On Track").sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "Capital Spend", f"${cap['actual_to_date']:.2f}M",
        f"{cap['actual_to_date'] / cap_env * 100:.0f}% of ${cap_env:.3f}M",
        delta_color="off", border=True,
    )
    c2.metric(
        "Operating Spend", f"${opx['actual_to_date']:.2f}M",
        f"{opx['actual_to_date'] / opx_env * 100:.0f}% of ${opx_env:.3f}M",
        delta_color="off", border=True,
    )
    c3.metric("Programme SPI", f"{evm['spi']:.2f}", *plan_delta(evm["spi"]),
              border=True)
    c4.metric("Programme CPI", f"{evm['cpi']:.2f}", *plan_delta(evm["cpi"]),
              border=True)
    c5.metric("Projects On Track", f"{on_track}/{len(projects)}",
              "of selected projects", delta_color="off", border=True)

    _health_banner(_programme_rag(evm["spi"], evm["cpi"]), evm["spi"],
                   evm["cpi"], as_at)

    envelope = (cap_env if "Capital" in expense_types else 0.0) + (
        opx_env if "Operating" in expense_types else 0.0
    )
    st.plotly_chart(
        _burndown_chart(monthly_rollup(fin_slice), envelope, as_at),
        use_container_width=True,
    )

    st.subheader("Project health")
    _health_table(project_evm_table(fin_slice, projects, as_at), phases)

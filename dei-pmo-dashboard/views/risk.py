"""Tab 2 - Risk Management: 5x5 likelihood x consequence matrix + register."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import (
    CONSEQUENCE_LABELS,
    INK_PRIMARY,
    INK_SECONDARY,
    LIKELIHOOD_LABELS,
    RISK_ZONES,
    SURFACE,
    ZONE_COLOURS,
)
from views.chart_theme import themed

_ZONE_NAMES = tuple(name for _, name in RISK_ZONES)
_CELL_ALPHA = 0.45


def zone_for(score: int) -> str:
    for ceiling, name in RISK_ZONES:
        if score <= ceiling:
            return name
    return _ZONE_NAMES[-1]


def _blend_to_surface(hex_colour: str, alpha: float) -> str:
    """Simulate `hex_colour` at `alpha` over the chart surface."""
    fg = tuple(int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    bg = tuple(int(SURFACE[i:i + 2], 16) for i in (1, 3, 5))
    mixed = tuple(round(b + (f - b) * alpha) for f, b in zip(fg, bg))
    return "#{:02x}{:02x}{:02x}".format(*mixed)


def _matrix_figure(projects: pd.DataFrame) -> go.Figure:
    counts = np.zeros((5, 5), dtype=int)
    for row in projects.itertuples():
        counts[row.likelihood - 1][row.consequence - 1] += 1

    zone_idx = np.array([
        [_ZONE_NAMES.index(zone_for((li + 1) * (ci + 1))) for ci in range(5)]
        for li in range(5)
    ])
    zone_names = [[_ZONE_NAMES[z] for z in row] for row in zone_idx]
    cell_text = [[str(c) if c else "" for c in row] for row in counts]

    blended = [_blend_to_surface(ZONE_COLOURS[name], _CELL_ALPHA)
               for name in _ZONE_NAMES]
    colorscale = []
    for i, colour in enumerate(blended):
        colorscale += [[i / 4, colour], [(i + 1) / 4, colour]]

    fig = go.Figure(go.Heatmap(
        z=zone_idx, zmin=0, zmax=4,
        x=[f"{i + 1} · {label}" for i, label in enumerate(CONSEQUENCE_LABELS)],
        y=[f"{i + 1} · {label}" for i, label in enumerate(LIKELIHOOD_LABELS)],
        colorscale=colorscale, showscale=False,
        xgap=2, ygap=2,
        text=cell_text, texttemplate="%{text}",
        textfont={"color": INK_PRIMARY, "size": 16},
        customdata=np.dstack([counts, zone_names]),
        hovertemplate=("Likelihood %{y} × Consequence %{x}<br>"
                       "%{customdata[1]} zone · %{customdata[0]} projects"
                       "<extra></extra>"),
    ))
    fig.update_layout(
        title={"text": "Portfolio risk matrix — project count per cell",
               "font": {"color": INK_SECONDARY, "size": 15}},
        xaxis={"title": "Consequence", "side": "bottom"},
        yaxis={"title": "Likelihood"},
    )
    return themed(fig, height=460)


def _zone_legend() -> None:
    parts = [
        f"<span style='color:{ZONE_COLOURS[name]};font-weight:700;'>■ {name}"
        f"</span> <span style='color:{INK_SECONDARY};'>≤ {ceiling}</span>"
        for ceiling, name in RISK_ZONES
    ]
    st.markdown(
        "<div style='margin:0.2rem 0 0.8rem 0;'>Zone (likelihood × consequence "
        "score): " + " &nbsp;·&nbsp; ".join(parts) + "</div>",
        unsafe_allow_html=True,
    )


def _risk_register(projects: pd.DataFrame) -> None:
    register = (
        projects.assign(zone=lambda d: d["risk_score"].map(zone_for))
        .loc[lambda d: d["zone"].isin(("High", "Extreme"))]
        .sort_values(["risk_score", "budget_m"], ascending=False)
        [["project_id", "name", "base", "priority", "likelihood",
          "consequence", "risk_score", "zone", "budget_m"]]
    )
    if register.empty:
        st.info("No projects in the High or Extreme zones under current filters.")
        return

    styler = (
        register.rename(columns={
            "project_id": "ID", "name": "Project", "base": "Base",
            "priority": "Priority", "likelihood": "L", "consequence": "C",
            "risk_score": "Score", "zone": "Zone", "budget_m": "Budget ($M)",
        })
        .style.map(
            lambda zone: f"color: {ZONE_COLOURS[zone]}; font-weight: 700",
            subset=["Zone"],
        )
        .format({"Budget ($M)": "{:.1f}"})
    )
    st.dataframe(styler, hide_index=True, use_container_width=True, height=420)


def render(projects: pd.DataFrame) -> None:
    st.plotly_chart(_matrix_figure(projects), use_container_width=True)
    _zone_legend()
    st.subheader(
        f"High & Extreme zone register "
        f"({int(projects['risk_score'].map(zone_for).isin(('High', 'Extreme')).sum())} "
        f"of {len(projects)} selected projects)"
    )
    _risk_register(projects)

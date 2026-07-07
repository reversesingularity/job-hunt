"""Shared Plotly layout for the dark navy surface."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
from config import GRIDLINE, INK_MUTED, INK_SECONDARY, SURFACE, SURFACE_CARD


def plan_delta(index_value: float) -> tuple[str, str]:
    """st.metric (delta, delta_color) for an SPI/CPI value vs the 1.0 baseline."""
    if abs(index_value - 1.0) < 0.005:
        return "on plan", "off"
    return f"{(index_value - 1) * 100:+.1f}% vs plan", "normal"


def themed(fig: go.Figure, *, height: int = 420, **overrides: Any) -> go.Figure:
    """Apply the validated dark-navy chart chrome to a figure."""
    layout: dict[str, Any] = {
        "paper_bgcolor": SURFACE,
        "plot_bgcolor": SURFACE,
        "font": {"family": "system-ui, 'Segoe UI', sans-serif",
                 "color": INK_SECONDARY, "size": 13},
        "height": height,
        "margin": {"l": 10, "r": 10, "t": 48, "b": 10},
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02,
                   "xanchor": "right", "x": 1},
        "hoverlabel": {"bgcolor": SURFACE_CARD, "font_color": "#e8eef5",
                       "bordercolor": GRIDLINE},
    }
    fig.update_layout(**{**layout, **overrides})
    fig.update_xaxes(gridcolor=GRIDLINE, linecolor=GRIDLINE, zeroline=False,
                     tickfont={"color": INK_MUTED})
    fig.update_yaxes(gridcolor=GRIDLINE, linecolor=GRIDLINE, zeroline=False,
                     tickfont={"color": INK_MUTED})
    return fig

"""Export hi-fidelity Plotly PNGs for the README documentation gallery."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

SURFACE = "#0e1b2c"
INK_PRIMARY = "#e8eef5"
INK_SECONDARY = "#c3c2b7"
INK_MUTED = "#898781"
GRIDLINE = "#24364d"
BLUE = "#3987e5"
AQUA = "#199e70"
STATUS = {
    "On Track": "#0ca30c",
    "At Risk": "#fab219",
    "Behind": "#d03b3b",
    "Complete": "#3987e5",
}
ZONE = {
    "Low": "#0ca30c",
    "Moderate": "#fab219",
    "High": "#ec835a",
    "Extreme": "#d03b3b",
}
LIKELIHOOD = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
CONSEQUENCE = ["Insignificant", "Minor", "Moderate", "Major", "Severe"]
PRIORITY_ORDER = ["Critical", "High", "Medium", "Low"]
ZONE_NAMES = ["Low", "Moderate", "High", "Extreme"]


def theme(fig: go.Figure, height: int = 480) -> go.Figure:
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font={"family": "Segoe UI, system-ui, sans-serif",
              "color": INK_SECONDARY, "size": 13},
        height=height,
        margin={"l": 60, "r": 40, "t": 70, "b": 50},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02,
                "xanchor": "right", "x": 1},
        title={"font": {"color": INK_PRIMARY, "size": 18}},
    )
    fig.update_xaxes(gridcolor=GRIDLINE, linecolor=GRIDLINE,
                     tickfont={"color": INK_MUTED})
    fig.update_yaxes(gridcolor=GRIDLINE, linecolor=GRIDLINE,
                     tickfont={"color": INK_MUTED})
    return fig


def zone_for(score: int) -> str:
    if score <= 4:
        return "Low"
    if score <= 9:
        return "Moderate"
    if score <= 16:
        return "High"
    return "Extreme"


def blend(hex_colour: str, alpha: float = 0.45) -> str:
    fg = tuple(int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    bg = tuple(int(SURFACE[i:i + 2], 16) for i in (1, 3, 5))
    mixed = tuple(round(b + (f - b) * alpha) for f, b in zip(fg, bg))
    return "#{:02x}{:02x}{:02x}".format(*mixed)


def main() -> None:
    projects = pd.read_csv(
        ROOT / "data" / "csv" / "projects.csv",
        parse_dates=["start_date", "end_date"],
    )
    financials = pd.read_csv(
        ROOT / "data" / "csv" / "financials.csv",
        parse_dates=["month_end"],
    )
    as_at = date(2026, 6, 30)

    counts = projects["priority"].value_counts().reindex(PRIORITY_ORDER).fillna(0)
    fig = go.Figure(go.Bar(
        x=list(counts.index), y=counts.to_numpy(), marker_color=BLUE,
        text=[int(v) for v in counts], textposition="outside",
        textfont={"color": INK_SECONDARY},
    ))
    fig.update_layout(
        title="Portfolio Priority Mix — 141 Projects (DEPP 2025 Shape)",
        showlegend=False, yaxis_title="Project count", xaxis_title="Priority",
    )
    theme(fig, 460).write_image(OUT / "priority-mix.png", scale=2, width=1100, height=460)

    totals = projects.groupby("base")["budget_m"].sum().sort_values()
    fig = go.Figure(go.Bar(
        x=totals.to_numpy(), y=list(totals.index), orientation="h",
        marker_color=BLUE,
    ))
    fig.update_layout(
        title="Budget by NZDF Base Location ($M)",
        showlegend=False,
        xaxis={"title": "Budget ($M)", "ticksuffix": "M"},
        yaxis_title=None,
    )
    theme(fig, 500).write_image(OUT / "budget-by-base.png", scale=2, width=1100, height=500)

    dom = projects.groupby("domain")["budget_m"].sum().sort_values(ascending=False)
    fig = go.Figure(go.Pie(
        labels=dom.index, values=dom.values, hole=0.55,
        marker={"colors": ["#3987e5", "#199e70", "#c98500", "#ec835a", "#7c6cf0", "#5aabb8"],
                "line": {"color": SURFACE, "width": 2}},
        textinfo="label+percent", textfont={"color": INK_PRIMARY},
    ))
    fig.update_layout(title="Portfolio Budget Share by Infrastructure Domain")
    theme(fig, 480).write_image(OUT / "domain-budget.png", scale=2, width=900, height=480)

    rag = projects["rag_status"].value_counts().reindex(
        ["On Track", "At Risk", "Behind", "Complete"]
    ).fillna(0)
    fig = go.Figure(go.Bar(
        x=list(rag.index), y=rag.to_numpy(),
        marker_color=[STATUS[k] for k in rag.index],
        text=[int(v) for v in rag], textposition="outside",
        textfont={"color": INK_SECONDARY},
    ))
    fig.update_layout(
        title="Delivery RAG Status (Synthetic EVM)",
        showlegend=False, yaxis_title="Projects", xaxis_title="Status",
    )
    theme(fig, 440).write_image(OUT / "rag-status.png", scale=2, width=1000, height=440)

    counts_m = np.zeros((5, 5), dtype=int)
    for row in projects.itertuples():
        counts_m[row.likelihood - 1][row.consequence - 1] += 1
    zone_idx = np.array([
        [ZONE_NAMES.index(zone_for((li + 1) * (ci + 1))) for ci in range(5)]
        for li in range(5)
    ])
    blended = [blend(ZONE[n]) for n in ZONE_NAMES]
    colorscale: list[list] = []
    for i, colour in enumerate(blended):
        colorscale += [[i / 4, colour], [(i + 1) / 4, colour]]
    cell_text = [[str(c) if c else "" for c in row] for row in counts_m]
    fig = go.Figure(go.Heatmap(
        z=zone_idx, zmin=0, zmax=4,
        x=[f"{i + 1} · {label}" for i, label in enumerate(CONSEQUENCE)],
        y=[f"{i + 1} · {label}" for i, label in enumerate(LIKELIHOOD)],
        colorscale=colorscale, showscale=False, xgap=2, ygap=2,
        text=cell_text, texttemplate="%{text}",
        textfont={"color": INK_PRIMARY, "size": 16},
    ))
    fig.update_layout(
        title="5×5 Portfolio Risk Matrix — Project Count per Cell",
        xaxis_title="Consequence", yaxis_title="Likelihood",
    )
    theme(fig, 520).write_image(OUT / "risk-matrix.png", scale=2, width=1100, height=520)

    top = projects.nlargest(10, "budget_m").copy()
    fig = px.timeline(
        top, x_start="start_date", x_end="end_date", y="name", color="rag_status",
        color_discrete_map=STATUS,
        category_orders={"rag_status": ["Complete", "On Track", "At Risk", "Behind"]},
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
        title="Top 10 by Budget — Delivery Schedule (Gantt)",
        legend_title_text="",
    )
    theme(fig, 520).write_image(OUT / "gantt-top10.png", scale=2, width=1200, height=520)

    ids = top["project_id"].tolist()
    fin = financials.loc[financials["project_id"].isin(ids)].copy()
    future = fin["month_end"] > pd.Timestamp(as_at)
    fin.loc[future, ["earned_m", "actual_m"]] = pd.NA
    rolled = (
        fin.groupby("month_end", as_index=False)[["planned_m", "earned_m", "actual_m"]]
        .sum(min_count=1)
        .sort_values("month_end")
    )
    for col in ("planned_m", "earned_m", "actual_m"):
        rolled[f"cum_{col}"] = rolled[col].cumsum()
    envelope = float(top["budget_m"].sum())
    remaining_planned = envelope - rolled["cum_planned_m"]
    actual = rolled.dropna(subset=["cum_actual_m"])
    remaining_actual = envelope - actual["cum_actual_m"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rolled["month_end"], y=remaining_planned, name="Planned remaining",
        mode="lines", line={"color": BLUE, "width": 2.5},
    ))
    fig.add_trace(go.Scatter(
        x=actual["month_end"], y=remaining_actual, name="Actual remaining",
        mode="lines", line={"color": AQUA, "width": 2.5},
    ))
    fig.add_shape(
        type="line", x0=as_at, x1=as_at, y0=0, y1=1, yref="paper",
        line={"color": INK_MUTED, "width": 1, "dash": "dot"},
    )
    fig.update_layout(
        title="Top 10 Budget Burndown — Envelope Remaining ($M)",
        yaxis={"ticksuffix": "M", "rangemode": "tozero",
               "title": "Remaining budget ($M)"},
        hovermode="x unified",
    )
    theme(fig, 440).write_image(OUT / "burndown.png", scale=2, width=1100, height=440)

    fig = go.Figure()
    for status, colour in STATUS.items():
        sub = projects.loc[projects["rag_status"] == status]
        fig.add_trace(go.Scatter(
            x=sub["spi"], y=sub["cpi"], mode="markers", name=status,
            marker={"color": colour, "size": 9, "opacity": 0.85, "line": {"width": 0}},
            text=sub["name"],
            hovertemplate="%{text}<br>SPI %{x:.2f} · CPI %{y:.2f}<extra></extra>",
        ))
    fig.add_hline(y=1.0, line={"color": INK_MUTED, "dash": "dot", "width": 1})
    fig.add_vline(x=1.0, line={"color": INK_MUTED, "dash": "dot", "width": 1})
    fig.add_shape(
        type="rect", x0=0.95, x1=1.2, y0=0.95, y1=1.2,
        fillcolor="rgba(12,163,12,0.08)", line_width=0,
    )
    fig.update_layout(
        title="Earned Value Performance — SPI vs CPI by Project",
        xaxis_title="Schedule Performance Index (SPI)",
        yaxis_title="Cost Performance Index (CPI)",
        xaxis={"range": [0.75, 1.25]}, yaxis={"range": [0.75, 1.25]},
    )
    theme(fig, 520).write_image(OUT / "spi-cpi-scatter.png", scale=2, width=1000, height=520)

    budget = float(projects["budget_m"].sum())
    to_date = financials.loc[financials["month_end"] <= pd.Timestamp(as_at)]
    pv = float(to_date["planned_m"].sum())
    ev = float(to_date["earned_m"].sum())
    ac = float(to_date["actual_m"].sum())
    spi = ev / pv if pv else 0.0
    cpi = ev / ac if ac else 0.0
    at_risk = int(projects["rag_status"].isin(["At Risk", "Behind"]).sum())
    kpis = [
        ("Total Portfolio Budget", f"${budget:,.0f}M"),
        ("Spend to Date", f"${ac:,.0f}M"),
        ("Portfolio SPI", f"{spi:.2f}"),
        ("Portfolio CPI", f"{cpi:.2f}"),
        ("Projects at Risk", f"{at_risk}"),
    ]
    fig = go.Figure()
    for i, (label, val) in enumerate(kpis):
        fig.add_annotation(
            x=i, y=0.55, text=f"<b>{val}</b>", showarrow=False,
            font={"size": 28, "color": INK_PRIMARY}, xref="x", yref="y",
        )
        fig.add_annotation(
            x=i, y=0.22, text=label, showarrow=False,
            font={"size": 13, "color": INK_MUTED}, xref="x", yref="y",
        )
    fig.update_xaxes(visible=False, range=[-0.5, 4.5])
    fig.update_yaxes(visible=False, range=[0, 1])
    fig.update_layout(title="Executive KPI Strip — Reporting as at June 2026 (Synthetic)")
    theme(fig, 220).write_image(OUT / "kpi-strip.png", scale=2, width=1200, height=220)

    print("Exported:", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()

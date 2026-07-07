"""Portfolio constants for the DE&I Horizontal Infrastructure PMO Dashboard.

Portfolio shape (141 projects; 24 Critical / 45 High / 72 Medium-Low) reflects
the 2025 Defence Estate Portfolio Plan; all delivery figures are synthetic.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Final

# --- Paths -------------------------------------------------------------------
ROOT_DIR: Final[Path] = Path(__file__).resolve().parent
DATA_DIR: Final[Path] = ROOT_DIR / "data"
DB_PATH: Final[Path] = DATA_DIR / "dei.duckdb"
CSV_DIR: Final[Path] = DATA_DIR / "csv"

# --- Portfolio shape (DEPP 2025) ----------------------------------------------
TOTAL_PROJECTS: Final[int] = 141
PRIORITY_COUNTS: Final[dict[str, int]] = {
    "Critical": 24,
    "High": 45,
    "Medium": 44,
    "Low": 28,  # Medium + Low = 72 per DEPP 2025
}
PRIORITY_ORDER: Final[tuple[str, ...]] = ("Critical", "High", "Medium", "Low")

BASES: Final[tuple[str, ...]] = (
    "Devonport", "Whenuapai", "Papakura", "Waiouru", "Linton",
    "Burnham", "Ohakea", "Trentham", "Woodbourne",
)
DOMAINS: Final[tuple[str, ...]] = (
    "Water", "Wastewater", "Stormwater", "Power", "ICT", "Roading",
)

# --- Reporting window ----------------------------------------------------------
PORTFOLIO_START: Final[date] = date(2024, 1, 1)
PORTFOLIO_END: Final[date] = date(2032, 6, 30)
AS_AT_DATE: Final[date] = date(2026, 6, 30)  # last complete reporting month

# --- RAG thresholds (applied to min(SPI, CPI)) ----------------------------------
RAG_GREEN_FLOOR: Final[float] = 0.95
RAG_AMBER_FLOOR: Final[float] = 0.85

# --- Risk matrix banding (score = likelihood x consequence) ---------------------
RISK_ZONES: Final[tuple[tuple[int, str], ...]] = (
    (4, "Low"), (9, "Moderate"), (16, "High"), (25, "Extreme"),
)
LIKELIHOOD_LABELS: Final[tuple[str, ...]] = (
    "Rare", "Unlikely", "Possible", "Likely", "Almost Certain",
)
CONSEQUENCE_LABELS: Final[tuple[str, ...]] = (
    "Insignificant", "Minor", "Moderate", "Major", "Severe",
)

# --- Validated chart palette (dark navy surface #0e1b2c) -------------------------
SURFACE: Final[str] = "#0e1b2c"
SURFACE_CARD: Final[str] = "#16283e"
INK_PRIMARY: Final[str] = "#e8eef5"
INK_SECONDARY: Final[str] = "#c3c2b7"
INK_MUTED: Final[str] = "#898781"
GRIDLINE: Final[str] = "#24364d"

SERIES: Final[dict[str, str]] = {
    "blue": "#3987e5",   # slot 1 - planned value
    "aqua": "#199e70",   # slot 2 - earned value / actual line
    "amber": "#c98500",  # slot 3 - actual cost
}

STATUS_COLOURS: Final[dict[str, str]] = {
    "On Track": "#0ca30c",
    "At Risk": "#fab219",
    "Behind": "#d03b3b",
    "Complete": "#3987e5",
}
STATUS_ICONS: Final[dict[str, str]] = {
    "On Track": "●",
    "At Risk": "▲",
    "Behind": "◆",
    "Complete": "■",
}

ZONE_COLOURS: Final[dict[str, str]] = {
    "Low": "#0ca30c",       # status good
    "Moderate": "#fab219",  # status warning
    "High": "#ec835a",      # status serious
    "Extreme": "#d03b3b",   # status critical
}

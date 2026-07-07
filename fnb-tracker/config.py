"""Programme constants for the FNB Tranche 1 Delivery Tracker.

Figures are sourced from the 2025 Defence Estate Portfolio Plan (DEPP) and
Budget 25 Cabinet approvals for Tranche 1a of the Future Naval Base programme.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Final

# --- Paths -----------------------------------------------------------------
ROOT_DIR: Final[Path] = Path(__file__).resolve().parent
DATA_DIR: Final[Path] = ROOT_DIR / "data"
DB_PATH: Final[Path] = DATA_DIR / "fnb.duckdb"
CSV_DIR: Final[Path] = DATA_DIR / "csv"

# --- Budget envelopes (Budget 25, FY26-FY29) --------------------------------
CAPITAL_BUDGET_M: Final[float] = 25.185
OPERATING_BUDGET_M: Final[float] = 5.375

# --- Programme window (NZ fiscal years: 1 Jul - 30 Jun) ----------------------
PROGRAMME_START: Final[date] = date(2025, 7, 1)   # FY26 opens
PROGRAMME_END: Final[date] = date(2029, 6, 30)    # FY29 closes
AS_AT_DATE: Final[date] = date(2026, 6, 30)       # last complete reporting month

# Tranche 1b construction funding gate - detailed business case in FY2028/29
T1B_GATE_DATE: Final[date] = date(2028, 11, 30)
T1B_GATE_LABEL: Final[str] = "Tranche 1b Construction DBC — FY28/29"

# --- RAG thresholds (applied to min(SPI, CPI)) -------------------------------
RAG_GREEN_FLOOR: Final[float] = 0.95
RAG_AMBER_FLOOR: Final[float] = 0.85

# --- Validated chart palette (dark navy surface #0e1b2c) ---------------------
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
    "Complete": "#3987e5",
    "On Track": "#0ca30c",
    "At Risk": "#fab219",
    "Behind": "#d03b3b",
    "Planned": "#898781",
}
STATUS_ICONS: Final[dict[str, str]] = {
    "Complete": "■",
    "On Track": "●",
    "At Risk": "▲",
    "Behind": "◆",
    "Planned": "○",
}

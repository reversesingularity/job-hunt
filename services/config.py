"""
Configuration for JobHunt.

Edit PROFILE and source lists to tune discovery and scoring.
All sources are public, read-only APIs — no scraping behind login walls.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
DB_PATH = os.environ.get("DATABASE_PATH", str(ROOT / "jobhunt.db"))
MASTER_CV_PATH = os.environ.get("MASTER_CV_PATH", str(DATA_DIR / "master_cv.json"))

# ---------------------------------------------------------------------------
# PROFILE — tune for bridge roles in NZ/AU defence/data
# ---------------------------------------------------------------------------
PROFILE = {
    "target_titles": [
        "data analyst", "bi analyst", "business intelligence",
        "data engineer", "analytics engineer", "reporting analyst",
        "technical support", "support engineer", "solutions engineer",
        "customer success", "solutions consultant", "data technician",
        "junior data", "associate data", "data quality",
    ],
    "exclude_titles": [
        "senior", "lead", "principal", "staff", "manager", "head of",
        "director", "architect", "chief", "vp ", "ii", "iii",
    ],
    "skills": [
        "python", "sql", "dbt", "duckdb", "postgresql", "postgres",
        "pandas", "numpy", "etl", "elt", "data pipeline", "fastapi",
        "power bi", "tableau", "streamlit", "docker", "git", "rag",
        "llm", "machine learning", "ai", "data warehouse", "snowflake",
        "azure", "aws", "data engineering", "api", "reporting",
        "dashboard", "stakeholder", "customer support", "automation",
    ],
    "hard_skills": [
        "python", "sql", "dbt", "duckdb", "postgresql", "postgres",
        "pandas", "numpy", "etl", "elt", "data pipeline", "fastapi",
        "docker", "git", "snowflake", "azure", "aws", "kubernetes",
        "spark", "machine learning", "rag", "llm",
    ],
    "preferred_locations": [
        "auckland", "wellington", "new zealand", "nz", "remote",
        "hybrid", "australia", "brisbane", "sydney", "melbourne",
        "adelaide", "canberra",
    ],
    "domain_bonus": [
        "defence", "defense", "aerospace", "space", "government",
        "security", "intelligence", "satellite", "rocket", "mission",
    ],
}

GREENHOUSE_BOARDS = [
    "rocketlab",
    "andurilindustries",
]

LEVER_ORGS: list[str] = []

ASHBY_BOARDS: list[str] = []

ADZUNA_COUNTRIES = ["nz", "au"]
ADZUNA_QUERIES = [
    "data analyst", "business intelligence", "technical support",
    "data engineer", "solutions engineer", "customer success",
]

# Company-name searches — catches Workday/Taleo employers (e.g. Lockheed Martin)
# with no public Greenhouse/Lever API.
ADZUNA_DEFENCE_QUERIES = [
    "Lockheed Martin",
    "BAE Systems",
    "Raytheon",
    "RTX",
    "Northrop Grumman",
    "Thales",
    "Saab",
    "Boeing",
    "L3Harris",
    "QinetiQ",
    "Leonardo",
    "General Dynamics",
    "defence contractor",
    "defense contractor",
    "aerospace defence",
    "aerospace defense",
]

# Friendly names for Greenhouse board slugs in output
GREENHOUSE_COMPANY_NAMES: dict[str, str] = {
    "rocketlab": "Rocket Lab",
    "andurilindustries": "Anduril Industries",
}

SCORE_THRESHOLD = 3
REQUIRE_TITLE_MATCH = True
TOP_N = 40
AUTO_APPLY_THRESHOLD = int(os.environ.get("AUTO_APPLY_THRESHOLD", "85"))
REQUIRE_APPROVAL = os.environ.get("REQUIRE_APPROVAL", "true").lower() == "true"

TAILOR_VOCAB = sorted(set(PROFILE["skills"] + [
    "machine learning", "data modelling", "data modeling", "data quality",
    "data visualisation", "data visualization", "reporting", "dashboards",
    "communication", "stakeholder", "problem solving", "process improvement",
    "power bi", "tableau", "looker", "snowflake", "bigquery", "azure", "aws",
    "ci/cd", "kubernetes", "rest api", "agile", "excel", "spark",
]))

SYNONYMS = {
    "etl": "etl", "elt": "etl", "data pipeline": "etl", "data pipelines": "etl",
    "powerbi": "power bi", "power-bi": "power bi", "power bi": "power bi", "bi": "power bi",
    "postgres": "postgresql", "postgresql": "postgresql",
    "data visualization": "data visualisation", "data visualisation": "data visualisation",
    "data modeling": "data modelling", "data modelling": "data modelling",
    "ml": "machine learning", "machine learning": "machine learning",
    "rest api": "api", "restful api": "api", "apis": "api", "api": "api",
    "dashboard": "dashboards", "dashboards": "dashboards",
    "stakeholder communication": "communication",
    "communications": "communication",
    "stakeholder management": "communication",
    "customer service": "customer support",
}

LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.1"))

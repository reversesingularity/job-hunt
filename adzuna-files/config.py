"""
Configuration for JobScout.

Everything here is meant to be edited by you. The profile drives the fit
scoring; the sources list drives where postings are pulled from. All sources
are public, read-only APIs — no scraping, no terms-of-service violations.
"""

# ---------------------------------------------------------------------------
# YOUR PROFILE  — tune these to change what scores highly
# ---------------------------------------------------------------------------
PROFILE = {
    # The role types you are realistically targeting NOW (bridge roles).
    # A posting whose title contains any of these gets a strong title match.
    "target_titles": [
        "data analyst", "bi analyst", "business intelligence",
        "data engineer", "analytics engineer", "reporting analyst",
        "technical support", "support engineer", "solutions engineer",
        "customer success", "solutions consultant", "data technician",
        "junior data", "associate data", "data quality",
    ],

    # Titles that signal too-senior roles — these are filtered out by default.
    "exclude_titles": [
        "senior", "lead", "principal", "staff", "manager", "head of",
        "director", "architect", "chief", "vp ", "ii", "iii",
    ],

    # Skills/keywords from your actual toolkit. Each one found in a job
    # description adds to the fit score and is shown back to you as evidence.
    "skills": [
        "python", "sql", "dbt", "duckdb", "postgresql", "postgres",
        "pandas", "numpy", "etl", "elt", "data pipeline", "fastapi",
        "power bi", "tableau", "streamlit", "docker", "git", "rag",
        "llm", "machine learning", "ai", "data warehouse", "snowflake",
        "azure", "aws", "data engineering", "api", "reporting",
        "dashboard", "stakeholder", "customer support", "automation",
    ],

    # Locations you'll consider. Matching adds to score; non-matching is
    # not excluded (it's just scored lower) so remote roles still surface.
    "preferred_locations": [
        "auckland", "wellington", "new zealand", "nz", "remote",
        "hybrid", "australia", "brisbane", "sydney", "melbourne",
        "adelaide", "canberra",
    ],

    # Domain words that earn a bonus — your strategic direction.
    "domain_bonus": [
        "defence", "defense", "aerospace", "space", "government",
        "security", "intelligence", "satellite", "rocket", "mission",
    ],
}

# ---------------------------------------------------------------------------
# SOURCES
# ---------------------------------------------------------------------------
# Greenhouse boards: the {token} is the company's job-board slug.
# API (no auth): https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true
# Add any defence/aerospace/data employer you find on job-boards.greenhouse.io.
GREENHOUSE_BOARDS = [
    "rocketlab",
    "andurilindustries",   # defence AI/autonomy, has an Australian arm
]

# Lever orgs: the {org} is the company's lever slug.
# API (no auth): https://api.lever.co/v0/postings/{org}?mode=json
LEVER_ORGS = [
    # e.g. "somecompany"
]

# Adzuna aggregates SEEK-style listings across NZ and AU and is the workhorse
# for broad coverage. Get a FREE key at https://developer.adzuna.com/ and put
# the values in environment variables ADZUNA_APP_ID and ADZUNA_APP_KEY.
ADZUNA_COUNTRIES = ["nz", "au"]
ADZUNA_QUERIES = [
    "data analyst", "business intelligence", "technical support",
    "data engineer", "solutions engineer", "customer success",
]

# Only keep postings scoring at or above this threshold.
SCORE_THRESHOLD = 3
# Require the job TITLE to match one of your target bridge-role types.
REQUIRE_TITLE_MATCH = True
# How many top roles to write out.
TOP_N = 40


# ---------------------------------------------------------------------------
# TAILORING — vocabulary and synonyms used to match a JD against your CV
# ---------------------------------------------------------------------------
# Canonical skill/keyword vocabulary the tailor looks for in a JD and your CV.
TAILOR_VOCAB = sorted(set(PROFILE["skills"] + [
    "machine learning", "data modelling", "data modeling", "data quality",
    "data visualisation", "data visualization", "reporting", "dashboards",
    "communication", "stakeholder", "problem solving", "process improvement",
    "power bi", "tableau", "looker", "snowflake", "bigquery", "azure", "aws",
    "ci/cd", "kubernetes", "rest api", "agile", "excel", "spark",
]))

# Map many surface forms to ONE canonical term so honest matches aren't missed
# (e.g. your "data pipeline" experience correctly satisfies a JD asking "ETL").
SYNONYMS = {
    "etl": "etl", "elt": "etl", "data pipeline": "etl", "data pipelines": "etl",
    "powerbi": "power bi", "power-bi": "power bi", "power bi": "power bi", "bi": "power bi",
    "postgres": "postgresql", "postgresql": "postgresql",
    "data visualization": "data visualisation", "data visualisation": "data visualisation",
    "data modeling": "data modelling", "data modelling": "data modelling",
    "ml": "machine learning", "machine learning": "machine learning",
    "rest api": "api", "restful api": "api", "apis": "api", "api": "api",
    "stakeholders": "stakeholder", "stakeholder": "stakeholder",
    "dashboard": "dashboards", "dashboards": "dashboards",
}

# Collapse stakeholder/communication surface forms to one canonical term so a
# decade of support experience is credited, not flagged as a gap.
SYNONYMS.update({
    "stakeholder communication": "communication",
    "stakeholder": "communication",
    "stakeholders": "communication",
    "communications": "communication",
    "stakeholder management": "communication",
    "customer service": "customer support",
})

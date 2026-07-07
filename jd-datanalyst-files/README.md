# JobScout

A terms-of-service-clean job aggregator and fit-scorer for a defence/data career
search across New Zealand and Australia. It pulls live postings from **public,
read-only job APIs**, scores each against your profile with fully transparent
logic, filters to the bridge roles you're actually targeting, and writes a
ranked shortlist plus editable cover-letter drafts.

No scraping. No LinkedIn automation. Nothing here can get an account banned —
that was a deliberate design choice (see the earlier discussion on why AIApply-
style scrapers are a legal and strategic dead end).

## What it does

- Fetches from **Greenhouse** and **Lever** company boards (no auth) and from
  **Adzuna** (free key) for whole-market NZ + AU coverage.
- Scores every posting transparently: title match (+4), each matching skill
  (+1, capped), preferred location (+2), strategic domain like defence/aerospace
  (+2), with a seniority gate that drops senior/lead/II/III roles.
- Requires a **bridge-role title match** by default, so you get data/analyst/
  support/customer-success roles — not engineering jobs above your current rung.
- Writes `output/shortlist.md`, `output/shortlist.csv`, and optional
  `output/cover_letters/*.md` drafts.

## Quickstart

```bash
pip install -r requirements.txt
python -m jobscout.run --drafts 5
```

Greenhouse/Lever run with no setup. For the NZ/AU whole-market coverage that
actually surfaces your bridge roles:

1. Get a free key at https://developer.adzuna.com/
2. Export it:
   ```bash
   export ADZUNA_APP_ID=your_id
   export ADZUNA_APP_KEY=your_key
   ```
3. Re-run. Adzuna queries NZ and AU for data analyst, BI, technical support,
   data engineer, solutions engineer, and customer success roles.

## Tuning it

Everything you'd change lives in `jobscout/config.py`:

- `PROFILE["target_titles"]` — the bridge roles you're chasing.
- `PROFILE["skills"]` — your toolkit; each hit is shown back as evidence.
- `PROFILE["domain_bonus"]` — your strategic direction (defence/aerospace/gov).
- `GREENHOUSE_BOARDS` / `LEVER_ORGS` — add employers as you find them on
  `job-boards.greenhouse.io` or `jobs.lever.co`.
- `REQUIRE_TITLE_MATCH` — set `False` to see a wider net.

## Important: what it can't see

Internal NZDF/MoD vacancies and many defence primes use closed ATS systems
(Workday, Taleo) with no public API. Those are a **manual** track — check the
internal Defence careers system yourself. This tool covers the open market.

## Design notes

The scoring is intentionally simple and explainable — no black-box model — so
you can justify every ranked result. Sources are public APIs returning their own
data; this is the lawful, durable alternative to scraping.

---

# CV Tailoring (`jobscout.tailor`)

Tailors your CV to a specific job description **without deception**. It works
from `master_cv.yml` — a file containing only true facts — and for each JD it
selects, reorders, and re-words *your real content* to fit. It cannot output
anything that isn't in your master file.

## Setup

1. Copy the template and fill it with your real details:
   ```bash
   cp master_cv.example.yml master_cv.yml
   ```
   Every line must be true. Set each skill `level` honestly (`core` / `working`
   / `familiar`) — this decides whether a match is reported as STRONG or PARTIAL.
2. Save a job description to a text file (e.g. `jd.txt`).

## Run

```bash
python -m jobscout.tailor --cv master_cv.yml --jd jd.txt
```

Outputs two files to `output/`:

- `coverage_*.md` — an honest report: **Strong matches** (lead with these),
  **Partial matches** (true, but own the depth), and **Gaps** (the JD wants it,
  your CV doesn't show it).
- `tailored_cv_*.md` — a CV draft assembled only from your real content, with
  bullets ordered by relevance to this JD and a tailored summary line.

## The non-deception guarantees

- Never adds a skill, bullet, or claim that isn't in your master CV.
- Never tells you to insert something untrue to "beat the ATS".
- Surfaces gaps instead of hiding them, with three honest options: address
  transferable evidence in a cover letter, learn it before applying, or accept
  the role is a stretch.
- Reports an **honest coverage %** — the share of JD terms you can genuinely
  evidence — so you know where a role really sits before you apply.

The fix to close a gap is always to make it true (learn the skill, do the
project), then update your master CV — not to write something you can't defend.

"""
CV tailoring — credible and non-deceptive by construction.

What it does:
  1. Reads your master CV (only-true-facts) and a job description.
  2. Reports honest coverage: STRONG matches (core skills / shown in real
     bullets), PARTIAL matches (working/familiar — own the depth honestly),
     and GAPS (the JD wants it, you don't have it).
  3. Produces a tailored CV draft assembled ONLY from your real content,
     selecting and ordering the bullets most relevant to this JD.

What it deliberately does NOT do:
  - It never adds a skill, bullet, or claim that isn't in your master CV.
  - It never tells you to insert something untrue to "beat the ATS".
  - Gaps are surfaced, not hidden, so you can address them in a cover letter,
    go and learn them, or decide the role is a stretch.

Usage:
    python -m jobscout.tailor --cv master_cv.yml --jd jd.txt
"""
import os
import re
import argparse

try:
    import yaml
except ImportError:
    raise SystemExit("Please: pip install pyyaml")

from . import config

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")


# ---------------------------------------------------------------------------
def canon(term: str) -> str:
    t = term.lower().strip()
    return config.SYNONYMS.get(t, t)


def terms_in_text(text: str):
    """Return the set of canonical vocab terms genuinely present in text."""
    low = " " + re.sub(r"\s+", " ", (text or "").lower()) + " "
    found = set()
    candidates = set(config.TAILOR_VOCAB) | set(config.SYNONYMS.keys())
    for term in candidates:
        # word-ish boundary match so "ai" doesn't match "available"
        if re.search(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", low):
            found.add(canon(term))
    return found


# ---------------------------------------------------------------------------
def cv_term_levels(cv: dict):
    """Map every canonical term you can evidence -> best level you hold.

    Declared skills use their stated level. Terms that only appear in your
    real bullets/projects (but weren't declared) are credited at 'working'
    because there is genuine evidence for them.
    """
    rank = {"core": 3, "working": 2, "familiar": 1}
    levels = {}

    def bump(term, level):
        term = canon(term)
        if rank.get(level, 0) > rank.get(levels.get(term, "none"), 0):
            levels[term] = level

    for s in cv.get("skills", []):
        bump(s["name"], s.get("level", "working"))

    # Evidence from real bullet text (experience + projects)
    for section in ("experience", "projects"):
        for item in cv.get(section, []):
            for b in item.get("bullets", []):
                for term in terms_in_text(b.get("text", "")):
                    bump(term, "working")
                for tag in b.get("skills", []):
                    bump(tag, "working")
    return levels


def classify(jd_terms, cv_levels):
    strong, partial, gap = [], [], []
    for t in sorted(jd_terms):
        lvl = cv_levels.get(t)
        if lvl == "core":
            strong.append(t)
        elif lvl in ("working", "familiar"):
            partial.append((t, lvl))
        else:
            gap.append(t)
    return strong, partial, gap


# ---------------------------------------------------------------------------
def rank_bullets(items, jd_terms):
    """Order each section's bullets by genuine relevance to this JD."""
    ranked = []
    for item in items:
        scored = []
        for b in item.get("bullets", []):
            bt = terms_in_text(b.get("text", "")) | {canon(x) for x in b.get("skills", [])}
            overlap = len(bt & jd_terms)
            scored.append((overlap, b.get("text", "")))
        scored.sort(key=lambda x: x[0], reverse=True)
        ranked.append((item, scored))
    # sort sections by their best bullet overlap
    ranked.sort(key=lambda x: max([s[0] for s in x[1]] or [0]), reverse=True)
    return ranked


def tailored_summary(cv, strong, partial):
    base = (cv.get("headline") or "").strip().rstrip(".")
    have = strong + [p[0] for p in partial]
    skills_line = ", ".join(have[:6])
    extra = f" Relevant strengths for this role: {skills_line}." if skills_line else ""
    return base + "." + extra


# ---------------------------------------------------------------------------
def build_reports(cv, jd_text):
    jd_terms = terms_in_text(jd_text)
    cv_levels = cv_term_levels(cv)
    strong, partial, gap = classify(jd_terms, cv_levels)
    covered = len(strong) + len(partial)
    pct = round(100 * covered / len(jd_terms)) if jd_terms else 0

    # ---- coverage report ----
    cov = []
    cov.append("# JD coverage report\n")
    cov.append("> This report uses ONLY what is in your master CV. Gaps are shown "
               "so you can address them honestly — never fabricate to fill them.\n")
    cov.append(f"**Honest keyword coverage: {pct}%** "
               f"({covered} of {len(jd_terms)} JD terms you can genuinely evidence)\n")

    cov.append("\n## Strong matches — lead with these")
    cov.append("\n".join(f"- {t}" for t in strong) or "- (none yet)")

    cov.append("\n## Partial matches — true, but own the depth honestly")
    cov.append("\n".join(f"- {t} _(your level: {lvl})_" for t, lvl in partial) or "- (none)")

    cov.append("\n## Gaps — the JD asks, your CV doesn't show it")
    if gap:
        cov.append("\n".join(f"- {t}" for t in gap))
        cov.append("\n_Options for each gap: address transferable evidence in your "
                   "cover letter, go and learn it before applying, or accept the "
                   "role is a stretch. Do not add it to your CV unless it becomes true._")
    else:
        cov.append("- (none — strong alignment)")

    # ---- tailored CV draft ----
    cv_md = []
    c = cv.get("contact", {})
    cv_md.append(f"# {cv.get('name','')}")
    cv_md.append(f"{cv.get('location','')} · {c.get('email','')} · {c.get('phone','')}")
    cv_md.append(f"{c.get('github','')} · {c.get('linkedin','')}\n")

    cv_md.append("## Summary")
    cv_md.append(tailored_summary(cv, strong, partial) + "\n")

    # skills reordered: JD-relevant true skills first
    relevant = strong + [p[0] for p in partial]
    others = [s["name"] for s in cv.get("skills", []) if canon(s["name"]) not in set(relevant)]
    cv_md.append("## Skills")
    cv_md.append(", ".join(relevant + others) + "\n")

    cv_md.append("## Experience")
    for item, scored in rank_bullets(cv.get("experience", []), jd_terms):
        cv_md.append(f"**{item.get('role','')}** — {item.get('employer','')} "
                     f"({item.get('start','')}–{item.get('end','')})")
        for _, text in scored:
            cv_md.append(f"- {text}")
        cv_md.append("")

    cv_md.append("## Projects")
    for item, scored in rank_bullets(cv.get("projects", []), jd_terms):
        cv_md.append(f"**{item.get('name','')}**")
        for _, text in scored:
            cv_md.append(f"- {text}")
        cv_md.append("")

    cv_md.append("## Education")
    for e in cv.get("education", []):
        cv_md.append(f"- {e.get('qualification','')}, {e.get('institution','')} ({e.get('year','')})")
    cv_md.append("\n## Certifications")
    for cert in cv.get("certifications", []):
        cv_md.append(f"- {cert}")

    return "\n".join(cov), "\n".join(cv_md), pct, gap


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cv", required=True, help="path to master CV yaml")
    ap.add_argument("--jd", required=True, help="path to job-description text file")
    args = ap.parse_args()

    cv = yaml.safe_load(open(args.cv))
    jd_text = open(args.jd).read()

    coverage_md, tailored_md, pct, gap = build_reports(cv, jd_text)

    os.makedirs(OUT_DIR, exist_ok=True)
    stem = re.sub(r"[^a-z0-9]+", "_", os.path.basename(args.jd).lower()).strip("_")[:40]
    cov_path = os.path.join(OUT_DIR, f"coverage_{stem}.md")
    cv_path = os.path.join(OUT_DIR, f"tailored_cv_{stem}.md")
    open(cov_path, "w").write(coverage_md)
    open(cv_path, "w").write(tailored_md)

    print(f"Honest coverage: {pct}%   Gaps: {len(gap)}")
    print(f"Wrote {cov_path}")
    print(f"Wrote {cv_path}")
    if gap:
        print("Gaps to handle truthfully:", ", ".join(gap))


if __name__ == "__main__":
    main()

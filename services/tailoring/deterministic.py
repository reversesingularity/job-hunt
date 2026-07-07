"""Deterministic honest CV tailoring — ported from JobScout tailor.py."""

from __future__ import annotations

import re
from typing import Any

from services import config


def canon(term: str) -> str:
    t = term.lower().strip()
    return config.SYNONYMS.get(t, t)


def terms_in_text(text: str) -> set[str]:
    low = " " + re.sub(r"\s+", " ", (text or "").lower()) + " "
    found: set[str] = set()
    candidates = set(config.TAILOR_VOCAB) | set(config.SYNONYMS.keys())
    for term in candidates:
        if re.search(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", low):
            found.add(canon(term))
    return found


def cv_term_levels(cv: dict[str, Any]) -> dict[str, str]:
    rank = {"core": 3, "working": 2, "familiar": 1}
    levels: dict[str, str] = {}

    def bump(term: str, level: str) -> None:
        term = canon(term)
        if rank.get(level, 0) > rank.get(levels.get(term, "none"), 0):
            levels[term] = level

    for s in cv.get("skills", []):
        bump(s["name"], s.get("level", "working"))

    for section in ("experience", "projects"):
        for item in cv.get(section, []):
            for b in item.get("bullets", []):
                for term in terms_in_text(b.get("text", "")):
                    bump(term, "working")
                for tag in b.get("skills", []):
                    bump(tag, "working")
    return levels


def classify(jd_terms: set[str], cv_levels: dict[str, str]) -> tuple[list, list, list]:
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


def rank_bullets(items: list, jd_terms: set[str]) -> list:
    ranked = []
    for item in items:
        scored = []
        for b in item.get("bullets", []):
            bt = terms_in_text(b.get("text", "")) | {canon(x) for x in b.get("skills", [])}
            overlap = len(bt & jd_terms)
            scored.append((overlap, b))
        scored.sort(key=lambda x: x[0], reverse=True)
        ranked.append((item, [s[1] for s in scored]))
    ranked.sort(
        key=lambda x: max([len(terms_in_text(b.get("text", "")) & jd_terms) for b in x[1]] or [0]),
        reverse=True,
    )
    return ranked


def tailored_summary(cv: dict, strong: list, partial: list) -> str:
    base = (cv.get("headline") or "").strip().rstrip(".")
    have = strong + [p[0] for p in partial]
    skills_line = ", ".join(have[:6])
    extra = f" Relevant strengths for this role: {skills_line}." if skills_line else ""
    return base + "." + extra


def build_reports(cv: dict[str, Any], jd_text: str) -> tuple[str, str, float, list[str], str]:
    jd_terms = terms_in_text(jd_text)
    cv_levels = cv_term_levels(cv)
    strong, partial, gap = classify(jd_terms, cv_levels)
    covered = len(strong) + len(partial)
    pct = round(100 * covered / len(jd_terms), 1) if jd_terms else 0.0
    summary = tailored_summary(cv, strong, partial)

    cov = ["# JD coverage report\n"]
    cov.append(
        "> Uses ONLY master_cv.json facts. Gaps are shown honestly — never fabricate.\n"
    )
    cov.append(
        f"**Honest keyword coverage: {pct}%** "
        f"({covered} of {len(jd_terms)} JD terms you can genuinely evidence)\n"
    )
    cov.append("\n## Strong matches — lead with these")
    cov.append("\n".join(f"- {t}" for t in strong) or "- (none yet)")
    cov.append("\n## Partial matches — true, but own the depth honestly")
    cov.append(
        "\n".join(f"- {t} _(your level: {lvl})_" for t, lvl in partial) or "- (none)"
    )
    cov.append("\n## Gaps — the JD asks, your CV doesn't show it")
    if gap:
        cov.append("\n".join(f"- {t}" for t in gap))
        cov.append(
            "\n_Options: address in cover letter, learn before applying, "
            "or accept the role is a stretch._"
        )
    else:
        cov.append("- (none — strong alignment)")

    cv_md = []
    c = cv.get("contact", {})
    cv_md.append(f"# {cv.get('name', '')}")
    cv_md.append(
        f"{cv.get('location', '')} · {c.get('email', '')} · {c.get('phone', '')}"
    )
    cv_md.append(f"{c.get('github', '')} · {c.get('linkedin', '')}\n")
    cv_md.append("## Summary")
    cv_md.append(summary + "\n")

    relevant = strong + [p[0] for p in partial]
    others = [s["name"] for s in cv.get("skills", []) if canon(s["name"]) not in set(relevant)]
    cv_md.append("## Skills")
    cv_md.append(", ".join(relevant + others) + "\n")

    cv_md.append("## Experience")
    for item, bullets in rank_bullets(cv.get("experience", []), jd_terms):
        cv_md.append(
            f"**{item.get('role', '')}** — {item.get('employer', '')} "
            f"({item.get('start', '')}–{item.get('end', '')})"
        )
        for b in bullets:
            cv_md.append(f"- {b.get('text', '')}")
        cv_md.append("")

    cv_md.append("## Projects")
    for item, bullets in rank_bullets(cv.get("projects", []), jd_terms):
        cv_md.append(f"**{item.get('name', '')}**")
        for b in bullets:
            cv_md.append(f"- {b.get('text', '')}")
        cv_md.append("")

    cv_md.append("## Education")
    for e in cv.get("education", []):
        cv_md.append(
            f"- {e.get('qualification', '')}, {e.get('institution', '')} "
            f"({e.get('year', '')})"
        )
    cv_md.append("\n## Certifications")
    for cert in cv.get("certifications", []):
        cv_md.append(f"- {cert}")

    return "\n".join(cov), "\n".join(cv_md), pct, gap, summary

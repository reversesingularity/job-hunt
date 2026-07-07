"""
Weighted compatibility scoring with explainable reasons.

Multipliers:
  2.0x — hard technical skills
  1.5x — title / function match
  1.0x — business context keywords (domain, stakeholder, etc.)
"""
from __future__ import annotations

from services import config

HARD_SKILL_MULT = 2.0
TITLE_MULT = 1.5
CONTEXT_MULT = 1.0
LOCATION_BONUS = 2.0
SENIORITY_PENALTY = -10.0
SKILL_CAP = 12


def _blob(p: dict) -> str:
    title = (p.get("title") or "").lower()
    loc = (p.get("location") or "").lower()
    desc = (p.get("description") or "").lower()
    return f"{title} {desc} {loc}"


def score_posting(p: dict) -> dict:
    title = (p.get("title") or "").lower()
    blob = _blob(p)

    score = 0.0
    reasons: list[str] = []

    too_senior = any(x in title for x in config.PROFILE["exclude_titles"])
    if too_senior:
        score += SENIORITY_PENALTY
        reasons.append("looks too senior")

    matched_titles = [t for t in config.PROFILE["target_titles"] if t in title]
    title_match = bool(matched_titles)
    if matched_titles:
        score += TITLE_MULT * 4
        reasons.append(f"role match (x{TITLE_MULT}): {matched_titles[0]}")

    hard_matched = sorted({s for s in config.PROFILE["hard_skills"] if s in blob})
    hard_points = min(len(hard_matched), SKILL_CAP) * HARD_SKILL_MULT
    score += hard_points
    if hard_matched:
        reasons.append(
            f"hard skills (x{HARD_SKILL_MULT}): {', '.join(hard_matched[:8])}"
        )

    soft_skills = set(config.PROFILE["skills"]) - set(config.PROFILE["hard_skills"])
    soft_matched = sorted({s for s in soft_skills if s in blob})
    soft_points = min(len(soft_matched), SKILL_CAP) * CONTEXT_MULT
    score += soft_points
    if soft_matched:
        reasons.append(f"context skills (x{CONTEXT_MULT}): {', '.join(soft_matched[:6])}")

    matched_loc = [loc for loc in config.PROFILE["preferred_locations"] if loc in blob]
    if matched_loc:
        score += LOCATION_BONUS
        reasons.append(f"location: {matched_loc[0]}")

    matched_domain = sorted({d for d in config.PROFILE["domain_bonus"] if d in blob})
    if matched_domain:
        score += CONTEXT_MULT * 2
        reasons.append(f"domain (x{CONTEXT_MULT}): {', '.join(matched_domain)}")

    matched_skills = sorted(set(hard_matched + soft_matched))

    return {
        "score": round(score, 2),
        "reasons": reasons,
        "matched_skills": matched_skills,
        "too_senior": too_senior,
        "title_match": title_match,
    }


def rank_postings(postings: list[dict]) -> list[dict]:
    scored = []
    for p in postings:
        s = score_posting(p)
        if s["too_senior"]:
            continue
        if config.REQUIRE_TITLE_MATCH and not s["title_match"]:
            continue
        if s["score"] >= config.SCORE_THRESHOLD:
            enriched = dict(p)
            enriched["_score"] = s["score"]
            enriched["_reasons"] = s["reasons"]
            enriched["_skills"] = s["matched_skills"]
            enriched["_too_senior"] = s["too_senior"]
            enriched["_title_match"] = s["title_match"]
            scored.append(enriched)
    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored[: config.TOP_N]

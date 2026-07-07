"""
Transparent fit scoring. No black-box model — every point is explainable,
which is exactly the property you want to be able to defend out loud.

Score components:
  +4   title contains one of your target role types
  +1   per skill found in the posting (capped)
  +2   location matches a preferred location
  +2   posting is in your strategic domain (defence/aerospace/gov)
  -10  title looks too senior (gates the role out)
"""
from .config import PROFILE

SKILL_CAP = 6


def score_posting(p: dict):
    title = (p.get("title") or "").lower()
    loc = (p.get("location") or "").lower()
    desc = (p.get("description") or "").lower()
    blob = f"{title} {desc} {loc}"

    score = 0
    reasons = []

    # Seniority gate
    too_senior = any(x in title for x in PROFILE["exclude_titles"])
    if too_senior:
        score -= 10
        reasons.append("looks too senior")

    # Target title match
    matched_titles = [t for t in PROFILE["target_titles"] if t in title]
    if matched_titles:
        score += 4
        reasons.append(f"role match: {matched_titles[0]}")

    # Skills evidence
    matched_skills = sorted({s for s in PROFILE["skills"] if s in blob})
    skill_points = min(len(matched_skills), SKILL_CAP)
    score += skill_points
    if matched_skills:
        reasons.append(f"skills: {', '.join(matched_skills[:8])}")

    # Location
    matched_loc = [l for l in PROFILE["preferred_locations"] if l in loc]
    if matched_loc:
        score += 2
        reasons.append(f"location: {matched_loc[0]}")

    # Domain bonus
    matched_domain = sorted({d for d in PROFILE["domain_bonus"] if d in blob})
    if matched_domain:
        score += 2
        reasons.append(f"domain: {', '.join(matched_domain)}")

    return {
        "score": score,
        "reasons": reasons,
        "matched_skills": matched_skills,
        "too_senior": too_senior,
        "title_match": bool(matched_titles),
    }

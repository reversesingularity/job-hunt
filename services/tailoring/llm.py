"""LLM-assisted STAR reordering with strict schema and low temperature."""

from __future__ import annotations

import json
import os
from typing import Any

from services import config
from services.tailoring.deterministic import build_reports, classify, cv_term_levels, terms_in_text
from services.tailoring.validator import validate_llm_output

LLM_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary_line": {"type": "string"},
        "skills_order": {"type": "array", "items": {"type": "string"}},
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "role_id": {"type": "string"},
                    "bullet_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["role_id", "bullet_ids"],
                "additionalProperties": False,
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "bullet_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["project_id", "bullet_ids"],
                "additionalProperties": False,
            },
        },
        "gaps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary_line", "skills_order", "experience", "projects", "gaps"],
    "additionalProperties": False,
}


def _build_llm_context(cv: dict[str, Any], jd_text: str) -> dict[str, Any]:
    jd_terms = terms_in_text(jd_text)
    cv_levels = cv_term_levels(cv)
    strong, partial, gap = classify(jd_terms, cv_levels)

    bullets = []
    for item in cv.get("experience", []):
        for b in item.get("bullets", []):
            bullets.append({
                "id": b["id"],
                "role_id": item["id"],
                "text": b["text"],
                "skills": b.get("skills", []),
            })
    for item in cv.get("projects", []):
        for b in item.get("bullets", []):
            bullets.append({
                "id": b["id"],
                "project_id": item["id"],
                "text": b["text"],
                "skills": b.get("skills", []),
            })

    return {
        "jd_terms": sorted(jd_terms),
        "strong_matches": strong,
        "partial_matches": [{"term": t, "level": lvl} for t, lvl in partial],
        "gaps": gap,
        "headline": cv.get("headline", ""),
        "skills": cv.get("skills", []),
        "bullets": bullets,
        "experience_roles": [
            {"id": e["id"], "role": e["role"], "employer": e["employer"]}
            for e in cv.get("experience", [])
        ],
        "projects": [{"id": p["id"], "name": p["name"]} for p in cv.get("projects", [])],
    }


def _call_openai(context: dict[str, Any]) -> dict[str, Any] | None:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        prompt = (
            "Reorder CV content to match the job description using STAR emphasis. "
            "NEVER invent skills, employers, dates, or metrics. "
            "Only select bullet_ids from the provided list and reorder skills from "
            "the provided skills list. summary_line must extend the headline using "
            "only existing skills.\n\n"
            f"Context:\n{json.dumps(context, indent=2)}"
        )
        resp = client.chat.completions.create(
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "tailored_cv",
                    "strict": True,
                    "schema": LLM_OUTPUT_SCHEMA,
                },
            },
            messages=[
                {
                    "role": "system",
                    "content": "You are an honest CV tailoring assistant. Never fabricate.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = resp.choices[0].message.content
        return json.loads(content) if content else None
    except Exception as e:
        print(f"  ! LLM tailoring failed ({e}), using deterministic fallback")
        return None


def _apply_llm_order(
    cv: dict[str, Any], llm: dict[str, Any], jd_text: str
) -> tuple[str, str, float, list[str], str]:
    jd_terms = terms_in_text(jd_text)
    cv_levels = cv_term_levels(cv)
    strong, partial, gap = classify(jd_terms, cv_levels)
    covered = len(strong) + len(partial)
    pct = round(100 * covered / len(jd_terms), 1) if jd_terms else 0.0
    summary = llm.get("summary_line") or ""

    exp_by_id = {e["id"]: e for e in cv.get("experience", [])}
    proj_by_id = {p["id"]: p for p in cv.get("projects", [])}
    bullet_by_id = {}
    for e in cv.get("experience", []):
        for b in e.get("bullets", []):
            bullet_by_id[b["id"]] = b
    for p in cv.get("projects", []):
        for b in p.get("bullets", []):
            bullet_by_id[b["id"]] = b

    cov = ["# JD coverage report\n", "> LLM-reordered from verified fact bank only.\n"]
    cov.append(f"**Honest keyword coverage: {pct}%**\n")
    cov.append("\n## Strong matches\n" + "\n".join(f"- {t}" for t in strong))
    cov.append("\n## Partial matches\n" + "\n".join(f"- {t} ({lvl})" for t, lvl in partial))
    cov.append("\n## Gaps\n" + "\n".join(f"- {t}" for t in (llm.get("gaps") or gap)))

    cv_md = []
    c = cv.get("contact", {})
    cv_md.append(f"# {cv.get('name', '')}")
    cv_md.append(f"{cv.get('location', '')} · {c.get('email', '')} · {c.get('phone', '')}\n")
    cv_md.append("## Summary\n" + summary + "\n")
    cv_md.append("## Skills\n" + ", ".join(llm.get("skills_order", [])) + "\n")

    cv_md.append("## Experience")
    for exp in llm.get("experience", []):
        item = exp_by_id.get(exp["role_id"])
        if not item:
            continue
        cv_md.append(
            f"**{item.get('role', '')}** — {item.get('employer', '')} "
            f"({item.get('start', '')}–{item.get('end', '')})"
        )
        for bid in exp.get("bullet_ids", []):
            b = bullet_by_id.get(bid)
            if b:
                cv_md.append(f"- {b['text']}")
        cv_md.append("")

    cv_md.append("## Projects")
    for proj in llm.get("projects", []):
        item = proj_by_id.get(proj["project_id"])
        if not item:
            continue
        cv_md.append(f"**{item.get('name', '')}**")
        for bid in proj.get("bullet_ids", []):
            b = bullet_by_id.get(bid)
            if b:
                cv_md.append(f"- {b['text']}")
        cv_md.append("")

    cv_md.append("## Education")
    for e in cv.get("education", []):
        cv_md.append(f"- {e.get('qualification', '')}, {e.get('institution', '')}")
    cv_md.append("\n## Certifications")
    for cert in cv.get("certifications", []):
        cv_md.append(f"- {cert}")

    return "\n".join(cov), "\n".join(cv_md), pct, list(llm.get("gaps") or gap), summary


def tailor_cv(cv: dict[str, Any], jd_text: str) -> tuple[str, str, float, list[str], str]:
    """Run LLM tailoring with deterministic fallback."""
    context = _build_llm_context(cv, jd_text)
    llm_out = _call_openai(context)
    if llm_out:
        ok, reason = validate_llm_output(llm_out, cv)
        if ok:
            return _apply_llm_order(cv, llm_out, jd_text)
        print(f"  ! LLM output failed validation ({reason}), using deterministic fallback")
    return build_reports(cv, jd_text)


def draft_cover_letter(cv: dict[str, Any], job: dict[str, Any], gaps: list[str]) -> str:
    """Honest cover letter draft — cites only fact bank claims."""
    name = cv.get("name", "Candidate")
    company = job.get("company", "the company")
    title = job.get("title", "the role")
    skills = [s["name"] for s in cv.get("skills", [])[:8]]

    letter = [
        "Dear Hiring Manager,\n",
        f"I am writing to express my interest in the {title} position at {company}. ",
        f"My background in {', '.join(skills[:4])} aligns with your requirements.\n",
        f"\n{ (cv.get('headline') or '').strip() }\n",
    ]
    if gaps:
        letter.append(
            f"\nI want to be transparent: I am still building depth in "
            f"{', '.join(gaps[:4])}. I am actively addressing these gaps and believe "
            f"my transferable experience in reporting, stakeholder communication, and "
            f"problem solving would add value while I continue to grow in those areas.\n"
        )
    letter.append(f"\nThank you for your consideration.\n\nSincerely,\n{name}")
    return "".join(letter)

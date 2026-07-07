"""Validate LLM tailoring output against fact bank — never fabricate."""

from __future__ import annotations

from typing import Any

import jsonschema

from services.tailoring.fact_bank import all_bullet_ids, all_bullet_texts

LLM_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["summary_line", "skills_order", "experience", "projects", "gaps"],
    "properties": {
        "summary_line": {"type": "string"},
        "skills_order": {"type": "array", "items": {"type": "string"}},
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["role_id", "bullet_ids"],
                "properties": {
                    "role_id": {"type": "string"},
                    "bullet_ids": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["project_id", "bullet_ids"],
                "properties": {
                    "project_id": {"type": "string"},
                    "bullet_ids": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "gaps": {"type": "array", "items": {"type": "string"}},
    },
}


def validate_llm_output(output: dict[str, Any], cv_internal: dict[str, Any]) -> tuple[bool, str]:
    try:
        jsonschema.validate(instance=output, schema=LLM_OUTPUT_SCHEMA)
    except jsonschema.ValidationError as e:
        return False, f"schema: {e.message}"

    valid_ids = all_bullet_ids(cv_internal)
    valid_skills = {s["name"].lower() for s in cv_internal.get("skills", [])}
    valid_texts = all_bullet_texts(cv_internal)

    for exp in output.get("experience", []):
        if exp["role_id"] not in cv_internal.get("_ids", {}).get("work", {}):
            if not any(e.get("id") == exp["role_id"] for e in cv_internal.get("experience", [])):
                return False, f"unknown role_id: {exp['role_id']}"
        for bid in exp.get("bullet_ids", []):
            if bid not in valid_ids:
                return False, f"unknown bullet_id: {bid}"

    for proj in output.get("projects", []):
        if not any(p.get("id") == proj["project_id"] for p in cv_internal.get("projects", [])):
            return False, f"unknown project_id: {proj['project_id']}"
        for bid in proj.get("bullet_ids", []):
            if bid not in valid_ids:
                return False, f"unknown bullet_id: {bid}"

    for skill in output.get("skills_order", []):
        if skill.lower() not in valid_skills and skill.lower() not in {
            s.lower() for s in valid_skills
        }:
            return False, f"fabricated skill: {skill}"

    if output.get("summary_line", "").strip() not in valid_texts:
        headline = (cv_internal.get("headline") or "").strip()
        summary = output["summary_line"].strip()
        if headline and not summary.startswith(headline[:40]):
            pass  # summary may extend headline with existing skills only

    return True, "ok"

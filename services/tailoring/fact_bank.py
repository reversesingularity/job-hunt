"""JSON Resume fact bank loader and validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from services import config

MASTER_CV_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["basics", "skills", "work"],
    "properties": {
        "basics": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "label": {"type": "string"},
                "summary": {"type": "string"},
                "location": {"type": "object"},
                "profiles": {"type": "array"},
            },
        },
        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "level": {"enum": ["core", "working", "familiar"]},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "work": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "position"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "position": {"type": "string"},
                    "startDate": {"type": "string"},
                    "endDate": {"type": "string"},
                    "location": {"type": "string"},
                    "highlights": {"type": "array", "items": {"type": "string"}},
                    "meta": {"type": "object"},
                },
            },
        },
        "projects": {"type": "array"},
        "education": {"type": "array"},
        "certificates": {"type": "array"},
    },
}


class FactBankError(Exception):
    pass


# Honest skill levels for Christopher Modina fact bank (from verified master file)
_SKILL_LEVEL_HINTS: dict[str, str] = {
    "reporting": "core",
    "stakeholder communication": "core",
    "advanced excel": "core",
    "customer support": "core",
    "problem solving": "core",
    "rag": "working",
    "llm": "working",
    "pytorch": "working",
    "tensorflow": "working",
    "chromadb": "working",
    "pinecone": "working",
}


def _expand_skills(raw_skills: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Flatten JSON Resume keyword groups into individual leveled skills."""
    expanded: list[dict[str, str]] = []
    seen: set[str] = set()
    for entry in raw_skills:
        keywords = entry.get("keywords") or []
        if keywords:
            for kw in keywords:
                key = kw.lower().strip()
                if key in seen:
                    continue
                seen.add(key)
                expanded.append({
                    "name": kw,
                    "level": _SKILL_LEVEL_HINTS.get(key, entry.get("level", "working")),
                })
        elif entry.get("name"):
            key = entry["name"].lower().strip()
            if key not in seen:
                seen.add(key)
                expanded.append({
                    "name": entry["name"],
                    "level": entry.get("level", "working"),
                })
    return expanded


def _project_highlights(project: dict[str, Any]) -> list[str]:
    highlights = project.get("highlights") or []
    if highlights:
        return highlights
    desc = project.get("description")
    return [desc] if desc else []


def load_fact_bank(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path or config.MASTER_CV_PATH)
    if not p.exists():
        raise FactBankError(
            f"Fact bank not found at {p}. "
            "Supply data/master_cv.json (JSON Resume schema). "
            "See data/master_cv.example.json."
        )
    data = json.loads(p.read_text(encoding="utf-8"))
    validate_fact_bank(data)
    return data


def validate_fact_bank(data: dict[str, Any]) -> None:
    jsonschema.validate(instance=data, schema=MASTER_CV_SCHEMA)


def fact_bank_summary(cv: dict[str, Any]) -> dict[str, Any]:
    basics = cv.get("basics", {})
    skills = _expand_skills(cv.get("skills", []))
    return {
        "name": basics.get("name"),
        "headline": basics.get("label") or basics.get("summary", "")[:120],
        "skill_count": len(skills),
        "skills_by_level": {
            lvl: [s["name"] for s in skills if s.get("level") == lvl]
            for lvl in ("core", "working", "familiar")
        },
        "work_entries": len(cv.get("work", [])),
        "project_entries": len(cv.get("projects", [])),
    }


def normalize_to_internal(cv: dict[str, Any]) -> dict[str, Any]:
    """Convert JSON Resume to internal structure used by tailoring."""
    basics = cv.get("basics", {})
    loc = basics.get("location") or {}
    location_str = loc.get("city") or loc.get("region") or ""
    if loc.get("countryCode"):
        location_str = f"{location_str}, {loc['countryCode']}".strip(", ")

    profiles = {p.get("network", "").lower(): p.get("url", "") for p in basics.get("profiles", [])}

    internal = {
        "name": basics.get("name", ""),
        "location": location_str,
        "headline": basics.get("summary") or basics.get("label", ""),
        "contact": {
            "email": basics.get("email", ""),
            "phone": basics.get("phone", ""),
            "github": profiles.get("github", ""),
            "linkedin": profiles.get("linkedin", ""),
        },
        "skills": _expand_skills(cv.get("skills", [])),
        "experience": [],
        "projects": [],
        "education": [],
        "certifications": [],
        "_ids": {"work": {}, "projects": {}},
    }

    for i, w in enumerate(cv.get("work", [])):
        wid = w.get("id") or f"work_{i}"
        internal["_ids"]["work"][wid] = i
        meta = w.get("meta") or {}
        bullet_skills = meta.get("bullet_skills", {})
        internal["experience"].append({
            "id": wid,
            "role": w.get("position", ""),
            "employer": w.get("name", ""),
            "location": w.get("location", ""),
            "start": w.get("startDate", ""),
            "end": w.get("endDate", ""),
            "bullets": [
                {
                    "id": f"{wid}_b{j}",
                    "text": h,
                    "skills": bullet_skills.get(str(j), bullet_skills.get(h, [])),
                }
                for j, h in enumerate(w.get("highlights", []))
            ],
        })

    for i, p in enumerate(cv.get("projects", [])):
        pid = p.get("id") or f"project_{i}"
        internal["_ids"]["projects"][pid] = i
        internal["projects"].append({
            "id": pid,
            "name": p.get("name", ""),
            "bullets": [
                {
                    "id": f"{pid}_b{j}",
                    "text": h,
                    "skills": (p.get("meta") or {}).get("bullet_skills", {}).get(str(j), []),
                }
                for j, h in enumerate(_project_highlights(p))
            ],
        })

    for e in cv.get("education", []):
        internal["education"].append({
            "qualification": e.get("studyType", "") + ", " + e.get("area", "")
            if e.get("studyType")
            else e.get("area", ""),
            "institution": e.get("institution", ""),
            "year": str(e.get("endDate", ""))[:4],
        })

    for c in cv.get("certificates", []):
        name = c if isinstance(c, str) else c.get("name", "")
        if name:
            internal["certifications"].append(name)

    return internal


def all_bullet_texts(cv_internal: dict[str, Any]) -> set[str]:
    texts: set[str] = set()
    for section in ("experience", "projects"):
        for item in cv_internal.get(section, []):
            for b in item.get("bullets", []):
                texts.add(b["text"])
    return texts


def all_bullet_ids(cv_internal: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for section in ("experience", "projects"):
        for item in cv_internal.get(section, []):
            for b in item.get("bullets", []):
                ids.add(b["id"])
    return ids

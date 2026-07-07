"""ATS-safe HTML and PDF rendering with embedded JSON Resume block."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fpdf import FPDF

from services import config


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _trim_bullets_for_one_page(cv_md: str, max_bullets: int = 12) -> str:
    """Drop lowest bullets from markdown if over budget (deterministic)."""
    lines = cv_md.split("\n")
    bullet_indices = [i for i, ln in enumerate(lines) if ln.startswith("- ")]
    if len(bullet_indices) <= max_bullets:
        return cv_md
    drop = set(bullet_indices[max_bullets:])
    return "\n".join(ln for i, ln in enumerate(lines) if i not in drop)


def md_to_html(cv_md: str, resume_json: dict[str, Any]) -> str:
    cv_md = _trim_bullets_for_one_page(cv_md)
    body_lines = []
    for line in cv_md.split("\n"):
        if line.startswith("# "):
            body_lines.append(f"<h1>{_escape_html(line[2:])}</h1>")
        elif line.startswith("## "):
            body_lines.append(f"<h2>{_escape_html(line[3:])}</h2>")
        elif line.startswith("- "):
            body_lines.append(f"<li>{_escape_html(line[2:])}</li>")
        elif line.startswith("**") and "**" in line[2:]:
            body_lines.append(f"<p><strong>{_escape_html(line)}</strong></p>")
        elif line.strip():
            body_lines.append(f"<p>{_escape_html(line)}</p>")

    json_ld = json.dumps(resume_json, indent=2)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{_escape_html(resume_json.get('basics', {}).get('name', 'CV'))}</title>
<style>
body {{ font-family: Arial, Calibri, sans-serif; font-size: 11pt; max-width: 700px;
       margin: 1in auto; line-height: 1.35; color: #222; }}
h1 {{ font-size: 18pt; color: #1F3864; text-align: center; margin-bottom: 0.2em; }}
h2 {{ font-size: 11pt; color: #1F3864; border-bottom: 1px solid #1F3864;
      text-transform: uppercase; margin-top: 1em; }}
li {{ margin-left: 1em; }}
p {{ margin: 0.2em 0; }}
</style>
<script type="application/ld+json">
{json_ld}
</script>
</head>
<body>
{"".join(body_lines)}
</body>
</html>"""


def html_to_pdf(html: str, pdf_path: Path) -> None:
    """Simple PDF via fpdf2 — body text only (excludes embedded JSON-LD block)."""
    body = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r"<style[^>]*>.*?</style>", "", body, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "\n", body)
    text = re.sub(r"\n+", "\n", text).strip()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    width = pdf.epw

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # fpdf2 built-in fonts are Latin-1; replace common unicode punctuation
        line = line.encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(width, 5, line)

    pdf.output(str(pdf_path))


def render_outputs(
    cv_md: str,
    resume_json: dict[str, Any],
    stem: str,
    output_dir: Path | None = None,
) -> tuple[str, str | None]:
    out = output_dir or config.OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    md_path = out / f"tailored_cv_{stem}.md"
    md_path.write_text(cv_md, encoding="utf-8")

    html = md_to_html(cv_md, resume_json)
    html_path = out / f"tailored_cv_{stem}.html"
    html_path.write_text(html, encoding="utf-8")

    pdf_path = out / f"tailored_cv_{stem}.pdf"
    try:
        html_to_pdf(html, pdf_path)
        return str(md_path), str(pdf_path)
    except Exception as e:
        print(f"  ! PDF generation failed ({e}), HTML written at {html_path}")
        return str(md_path), None

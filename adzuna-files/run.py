"""
JobScout — pull current postings from public job APIs, score them against your
profile, and write a ranked shortlist plus cover-letter drafts.

Usage:
    python -m jobscout.run                 # fetch, score, write shortlist
    python -m jobscout.run --drafts 5      # also draft 5 cover letters

Adzuna (broad NZ/AU coverage) activates when ADZUNA_APP_ID and ADZUNA_APP_KEY
are set. Without them, Greenhouse/Lever still run so you can see it work.
"""
import os
import csv
import argparse

from . import sources, config
from .score import score_posting
from .cover_letter import draft_cover_letter

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")


def gather():
    postings = []
    print("Fetching sources...")
    for board in config.GREENHOUSE_BOARDS:
        got = sources.from_greenhouse(board)
        print(f"  greenhouse:{board} -> {len(got)}")
        postings += got
    for org in config.LEVER_ORGS:
        got = sources.from_lever(org)
        print(f"  lever:{org} -> {len(got)}")
        postings += got

    app_id, app_key = sources.adzuna_keys()
    if app_id and app_key:
        for country in config.ADZUNA_COUNTRIES:
            for q in config.ADZUNA_QUERIES:
                got = sources.from_adzuna(country, q, app_id, app_key)
                print(f"  adzuna:{country}:{q} -> {len(got)}")
                postings += got
    else:
        print("  (Adzuna skipped — set ADZUNA_APP_ID and ADZUNA_APP_KEY for "
              "broad NZ/AU coverage)")
    return postings


def dedupe(postings):
    seen, out = set(), []
    for p in postings:
        key = p.get("url") or (p.get("company"), p.get("title"), p.get("location"))
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def rank(postings):
    scored = []
    for p in postings:
        s = score_posting(p)
        if s["too_senior"]:
            continue
        if config.REQUIRE_TITLE_MATCH and not s["title_match"]:
            continue
        if s["score"] >= config.SCORE_THRESHOLD:
            p["_score"] = s["score"]
            p["_reasons"] = s["reasons"]
            p["_skills"] = s["matched_skills"]
            scored.append(p)
    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored[: config.TOP_N]


def write_outputs(ranked, drafts=0):
    os.makedirs(OUT_DIR, exist_ok=True)

    md = os.path.join(OUT_DIR, "shortlist.md")
    with open(md, "w") as f:
        f.write(f"# Job shortlist ({len(ranked)} roles)\n\n")
        for i, p in enumerate(ranked, 1):
            f.write(f"## {i}. {p['title']} — {p['company'].title()}\n")
            f.write(f"- **Fit score:** {p['_score']}\n")
            f.write(f"- **Location:** {p.get('location') or 'n/a'}\n")
            f.write(f"- **Why:** {'; '.join(p['_reasons'])}\n")
            f.write(f"- **Link:** {p.get('url')}\n\n")

    csv_path = os.path.join(OUT_DIR, "shortlist.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["score", "title", "company", "location", "url"])
        for p in ranked:
            w.writerow([p["_score"], p["title"], p["company"],
                        p.get("location"), p.get("url")])

    if drafts:
        d_dir = os.path.join(OUT_DIR, "cover_letters")
        os.makedirs(d_dir, exist_ok=True)
        for p in ranked[:drafts]:
            safe = "".join(c for c in f"{p['company']}_{p['title']}"
                           if c.isalnum() or c in " -_")[:60].strip().replace(" ", "_")
            with open(os.path.join(d_dir, f"{safe}.md"), "w") as f:
                f.write(draft_cover_letter(p, p["_skills"]))

    print(f"\nWrote {md}")
    print(f"Wrote {csv_path}")
    if drafts:
        print(f"Wrote {drafts} cover-letter drafts to {OUT_DIR}/cover_letters/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drafts", type=int, default=0,
                    help="number of cover-letter drafts to generate")
    args = ap.parse_args()

    postings = gather()
    print(f"\nTotal fetched: {len(postings)}")
    postings = dedupe(postings)
    print(f"After dedupe:  {len(postings)}")
    ranked = rank(postings)
    print(f"Made shortlist: {len(ranked)} (score >= {config.SCORE_THRESHOLD})")
    write_outputs(ranked, drafts=args.drafts)


if __name__ == "__main__":
    main()

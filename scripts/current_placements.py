from services.db import get_conn, init_db, list_shortlist

init_db()

print("=== TOP 15 — ALL REGIONS ===")
all_jobs = list_shortlist(15)
for p in all_jobs:
    loc = (p.get("location") or "n/a")[:45]
    print(f"{p['score']:5.1f} | {p['company'][:22]:22} | {p['title'][:40]:40} | {loc}")

print("\n=== TOP 15 — AU/NZ ONLY (--location au,nz) ===")
local = list_shortlist(15, location_codes=["au", "nz"])
for p in local:
    loc = (p.get("location") or "n/a")[:45]
    reasons = "; ".join(p.get("reasons", [])[:2])
    print(f"{p['score']:5.1f} | {p['company'][:22]:22} | {p['title'][:40]:40} | {loc}")
    if reasons:
        print(f"         -> {reasons}")

print(f"\nTotals: {len(all_jobs)} shown (global top 15), {len(local)} AU/NZ (top 15 cap)")

with get_conn() as c:
    tailored = c.execute(
        "SELECT COUNT(*) FROM tailored_outputs"
    ).fetchone()[0]
    total_scored = c.execute(
        "SELECT COUNT(*) FROM job_scores WHERE score >= 3 AND too_senior = 0"
    ).fetchone()[0]
print(f"DB: {total_scored} qualifying scores (>=3), {tailored} tailored outputs on disk")

from services.db import init_db, list_shortlist

init_db()
s = list_shortlist(10, location_codes=["au", "nz"])
print(f"AU/NZ shortlist: {len(s)} jobs\n")
for p in s:
    loc = (p.get("location") or "")[:40]
    print(f"{p['score']:5.1f} | {p['company'][:22]:22} | {p['title'][:42]:42} | {loc}")

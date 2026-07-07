from services.db import get_conn, init_db

init_db()
with get_conn() as c:
    au = c.execute(
        """
        SELECT title, location, url FROM jobs
        WHERE company = 'andurilindustries'
          AND (location LIKE '%Australia%' OR location LIKE '%Sydney%'
               OR location LIKE '%Melbourne%' OR location LIKE '%Canberra%'
               OR location LIKE '%Brisbane%')
        ORDER BY title
        """
    ).fetchall()
    data = c.execute(
        """
        SELECT title, location, url FROM jobs
        WHERE company = 'andurilindustries'
          AND (location LIKE '%Australia%' OR location LIKE '%New Zealand%')
          AND (lower(title) LIKE '%data%'
               OR lower(title) LIKE '%analyst%'
               OR lower(title) LIKE '%analytics%'
               OR lower(title) LIKE '%support%'
               OR lower(title) LIKE '%reporting%')
        ORDER BY title
        """
    ).fetchall()
    us = c.execute(
        "SELECT COUNT(*) FROM jobs WHERE company='andurilindustries'"
    ).fetchone()[0]

print(f"Total Anduril in DB: {us}")
print(f"Australia-tagged: {len(au)}\n")
print("Data/analytics/support roles (AU/NZ):")
for title, loc, url in data:
    print(f"  {loc} | {title}")
print(f"  count: {len(data)}")

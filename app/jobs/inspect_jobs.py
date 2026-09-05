import sqlite3


conn = sqlite3.connect("data/jobs.db")

rows = conn.execute(
    """
    SELECT company, title, location, description
    FROM jobs
    WHERE title LIKE '%Frontend Engineer%'
       OR title LIKE '%Full Stack Engineer%'
       OR title LIKE '%Full Stack Software Engineer%'
    LIMIT 20
    """
).fetchall()

for company, title, location, description in rows:
    print("\n" + "=" * 80)
    print(f"{company} | {title} | {location}")
    print("-" * 80)
    print(description[:2500])

conn.close()
import sqlite3

from app.jobs.filter import filter_reason


conn = sqlite3.connect("data/jobs.db")
conn.row_factory = sqlite3.Row

rows = conn.execute(
    """
    SELECT company, title, location, description
    FROM jobs
    ORDER BY company, title
    """
).fetchall()

reasons = {}

for row in rows:
    job = {
        "title": row["title"],
        "location": {
            "name": row["location"] or ""
        },
        "content": row["description"] or "",
    }

    reason = filter_reason(job)

    if reason is None:
        reason = "RELEVANT"

    reasons[reason] = reasons.get(reason, 0) + 1


print("\n" + "=" * 80)
print("FILTER DIAGNOSTIC")
print("=" * 80)

for reason, count in sorted(
    reasons.items(),
    key=lambda item: item[1],
    reverse=True,
):
    print(f"{count:4} | {reason}")


print("\n" + "=" * 80)
print("PROMISING JOBS THAT ARE BEING REJECTED")
print("=" * 80)

keywords = [
    "frontend",
    "front-end",
    "react",
    "next.js",
    "full stack",
    "full-stack",
    "web developer",
    "software engineer",
]

shown = 0

for row in rows:
    title = row["title"].lower()

    if not any(keyword in title for keyword in keywords):
        continue

    job = {
        "title": row["title"],
        "location": {
            "name": row["location"] or ""
        },
        "content": row["description"] or "",
    }

    reason = filter_reason(job)

    if reason is None:
        continue

    print(
        f"{row['company']} | "
        f"{row['title']} | "
        f"{row['location'] or 'N/A'} | "
        f"{reason}"
    )

    shown += 1

    if shown >= 50:
        break


conn.close()
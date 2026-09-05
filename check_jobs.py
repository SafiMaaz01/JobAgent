import sqlite3

conn = sqlite3.connect("data/jobs.db")
cursor = conn.cursor()

row = cursor.execute(
    """
    SELECT id, company, title, location, description, recommendation, review_status
    FROM jobs
    WHERE id = 3379
    """
).fetchone()

print("ID:", row[0])
print("Company:", row[1])
print("Title:", row[2])
print("Location:", row[3])
print("Recommendation:", row[5])
print("Review status:", row[6])
print()
print("DESCRIPTION")
print("=" * 80)
print(row[4])

conn.close()
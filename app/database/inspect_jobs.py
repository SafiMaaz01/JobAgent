from app.database.db import get_connection


def main():
    connection = get_connection()

    jobs = connection.execute("""
        SELECT
            id,
            company,
            title,
            location,
            url,
            description,
            match_score,
            recommendation
        FROM jobs
        WHERE is_relevant = 1
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    for job in jobs:
        print("=" * 100)
        print(f"ID: {job['id']}")
        print(f"Company: {job['company']}")
        print(f"Title: {job['title']}")
        print(f"Location: {job['location']}")
        print(f"Score: {job['match_score']}")
        print(f"Recommendation: {job['recommendation']}")
        print(f"URL: {job['url']}")
        print("\nJOB DESCRIPTION:\n")
        print(job["description"])
        print()


if __name__ == "__main__":
    main()
    
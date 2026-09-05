from html.parser import HTMLParser


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts).strip()


def html_to_text(html):
    if not html:
        return ""

    parser = HTMLTextExtractor()
    parser.feed(html)

    return parser.get_text()


def normalize_greenhouse_job(job, company):
    return {
        "source": "greenhouse",
        "external_id": str(job["id"]),

        "company": company,

        "title": job.get("title", "").strip(),

        "location": (
            job.get("location", {}).get("name", "").strip()
        ),

        "url": job.get("absolute_url", ""),

        "description": html_to_text(
            job.get("content", "")
        ),

        "posted_at": job.get("first_published", ""),

        "updated_at": job.get("updated_at", ""),
    }
"""Local AI Job Matcher.

Evaluates job descriptions against the candidate's profile in data/profile.json
using a local LLM hosted via Ollama (e.g., qwen2.5:7b). Produces structured match
assessments with score (0-100), recommendation (APPLY / PASS), and detailed reasoning.
"""
import json
import requests
from pathlib import Path


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"

PROFILE_FILE = Path("data/profile.json")


def load_profile():
    """Load candidate profile information from data/profile.json."""
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def ask_ai(prompt: str) -> str:
    """Send an inference query to local Ollama instance and return raw response string."""
    response = requests.post(

        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=180
    )

    response.raise_for_status()

    return response.json()["response"]


def analyze_job(job_description: str):
    profile = load_profile()

    prompt = f"""
You are an expert recruitment matching agent.

Your job is to evaluate whether a candidate should apply
to a particular job.

IMPORTANT RULES:

1. Only use information present in the candidate profile.
2. Never invent experience, skills, qualifications, or achievements.
3. Distinguish between strong matches and missing requirements.
4. Be honest about gaps.
5. Give a score from 0 to 100.
6. Return ONLY valid JSON.

CANDIDATE PROFILE:

{json.dumps(profile, indent=2)}

JOB DESCRIPTION:

{job_description}

Return exactly this structure:

{{
  "match_score": 0,
  "recommendation": "APPLY",
  "strong_matches": [],
  "missing_requirements": [],
  "concerns": [],
  "reason": ""
}}

Recommendation must be one of:

"APPLY"
"REVIEW"
"SKIP"
"""

    return ask_ai(prompt)


if __name__ == "__main__":

    test_job = """
    Frontend Developer

    We are looking for a Junior Frontend Developer to join our team.

    Requirements:
    - Strong experience with React.js
    - Strong experience with Next.js
    - JavaScript and TypeScript
    - HTML and CSS
    - Tailwind CSS
    - REST API integration
    - Git and GitHub
    - Experience building responsive web applications

    Nice to have:
    - Redux
    - PostgreSQL
    - Firebase
    - Experience with modern authentication systems
    """

    result = analyze_job(test_job)

    print("\n===== JOB MATCH RESULT =====\n")
    print(result)
"""
Fact-constrained resume tailoring engine.

Orchestrates deterministic requirement extraction, fact verification against profile.json,
prioritized fact assembly, anti-fabrication validation, and ATS scoring.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import requests

from app.resume.extractor import extract_job_requirements
from app.resume.matcher import match_candidate_facts
from app.resume.validator import validate_resume
from app.resume.ats_scorer import compute_ats_score
from app.resume.aliases import normalize_skill

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"
DEFAULT_PROFILE_PATH = Path("data/profile.json")


def load_candidate_profile(profile_path: Optional[Path] = None) -> Dict[str, Any]:
    """Loads ground truth candidate profile from JSON file."""
    p_path = profile_path or DEFAULT_PROFILE_PATH
    if not p_path.exists():
        raise FileNotFoundError(f"Candidate profile not found at {p_path}")
    with open(p_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_tailored_summary(
    profile: Dict[str, Any],
    job: Dict[str, Any],
    matched_facts: Dict[str, Any],
    use_llm: bool = True,
) -> str:
    """
    Generates a professional summary highlighting verified skills matching the target role.
    Uses deterministic profile-backed summary as base or fallback.
    """
    matched_skills = matched_facts.get("all_matched_skills", [])
    top_skills_str = ", ".join(matched_skills[:4]) if matched_skills else "Next.js, React.js, and TypeScript"
    
    # Base deterministic summary
    target_role = job.get("title", "Frontend Developer")
    base_summary = (
        f"{target_role} with hands-on experience building scalable, responsive web applications "
        f"using {top_skills_str}. Experienced in state management, REST API integration, and performance "
        f"optimization with a strong focus on clean code and modern component architecture."
    )
    
    if not use_llm:
        return base_summary
        
    prompt = f"""You are a professional resume assistant. Write a concise 2-sentence professional summary for a resume.

GROUND TRUTH CANDIDATE PROFILE:
Candidate Name: {profile.get('name')}
Candidate Skills: {', '.join(profile.get('skills', []))}
Target Role: {job.get('title')}
Company: {job.get('company')}
Matched Verified Skills: {top_skills_str}
Base Profile Summary: {profile.get('summary')}

STRICT RULES:
1. NEVER invent any skill, tool, metric, years of experience, or achievement not present in the candidate profile.
2. Focus ONLY on verified skills: {top_skills_str}.
3. Keep it under 50 words.
4. Output ONLY the summary text, no explanations, no quotes.
"""
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            },
            timeout=10,
        )
        if resp.status_code == 200:
            ai_text = resp.json().get("response", "").strip()
            # Clean quotes or headers
            ai_text = ai_text.replace('"', '').strip()
            if len(ai_text.split()) >= 15 and len(ai_text.split()) <= 70:
                return ai_text
    except Exception as e:
        logger.warning(f"Ollama tailoring assist skipped or failed ({e}); using deterministic summary.")
        
    return base_summary


def generate_tailored_resume(
    job: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
    use_llm: bool = True,
) -> Dict[str, Any]:
    """
    Authoritative resume tailoring pipeline:
    1. Extracts job requirements & isolates domain terms.
    2. Matches candidate facts with strict trace pointers.
    3. Assembles tailored, prioritized resume structure.
    4. Runs anti-fabrication safety validation.
    5. Computes 100% deterministic ATS score.
    """
    if profile is None:
        profile = load_candidate_profile()

    job_title = job.get("title", "")
    job_desc = job.get("description", "")
    
    # 1. Deterministic Extraction
    job_reqs = extract_job_requirements(job_title, job_desc)
    
    # 2. Fact Matching & Traceability
    matched_facts = match_candidate_facts(profile, job_reqs)
    
    # 3. Resume Assembly
    summary_text = generate_tailored_summary(profile, job, matched_facts, use_llm=use_llm)
    
    # Prioritize skills: matched first, then remaining
    prioritized_skills = []
    seen_skills = set()
    for s_info in matched_facts.get("traced_skills", []):
        s_name = s_info["name"]
        if s_info["is_matched"] and s_name not in seen_skills:
            prioritized_skills.append(s_info)
            seen_skills.add(s_name)
    for s_info in matched_facts.get("traced_skills", []):
        s_name = s_info["name"]
        if s_name not in seen_skills:
            prioritized_skills.append(s_info)
            seen_skills.add(s_name)
            
    # Assembly structure
    tailored_resume_data = {
        "contact": {
            "name": profile.get("name", ""),
            "email": profile.get("email", ""),
            "phone": profile.get("phone", ""),
            "location": profile.get("location", ""),
            "linkedin": profile.get("linkedin", ""),
            "github": profile.get("github", ""),
            "portfolio": profile.get("portfolio", ""),
        },
        "target_role": job_title,
        "summary": summary_text,
        "skills": prioritized_skills,
        "experience": matched_facts.get("traced_experiences", []),
        "projects": matched_facts.get("traced_projects", []),
        "education": matched_facts.get("traced_education", []),
    }
    
    # 4. Anti-fabrication Validation
    validation_result = validate_resume(tailored_resume_data, profile)
    
    # If any error occurred in summary or tailoring, fallback to standard profile summary
    if not validation_result["is_valid"]:
        logger.warning("Tailoring validation failed on LLM draft; falling back to canonical profile data.")
        tailored_resume_data["summary"] = profile.get("summary", "")
        validation_result = validate_resume(tailored_resume_data, profile)

    # 5. Deterministic ATS Scoring
    ats_analysis = compute_ats_score(tailored_resume_data, job_reqs, matched_facts)
    
    return {
        "job_id": job.get("id"),
        "company": job.get("company"),
        "title": job.get("title"),
        "job_requirements": job_reqs,
        "matched_facts": {
            "matched_required": matched_facts.get("matched_required_skills", []),
            "missing_required": matched_facts.get("missing_required_skills", []),
            "matched_preferred": matched_facts.get("matched_preferred_skills", []),
            "missing_preferred": matched_facts.get("missing_preferred_skills", []),
        },
        "resume_data": tailored_resume_data,
        "validation": validation_result,
        "ats_analysis": ats_analysis,
    }

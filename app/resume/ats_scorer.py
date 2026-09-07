"""
100% Deterministic ATS scoring engine for JobAgent V2.

Computes a transparent, reproducible 0–100 ATS score and breakdown without LLM variance.
"""

from typing import Dict, List, Any, Set
from app.resume.aliases import are_skills_equivalent, normalize_skill


def compute_ats_score(
    resume_data: Dict[str, Any],
    job_reqs: Dict[str, Any],
    matched_facts: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Computes deterministic ATS score (0-100) and actionable breakdown.
    """
    breakdown = {
        "structural_compliance": 0,    # Max 25
        "required_keyword_match": 0,   # Max 35
        "preferred_keyword_match": 0,  # Max 15
        "completeness_length": 0,      # Max 15
        "parsing_health": 0,           # Max 10
    }
    
    recommendations: List[str] = []
    
    # 1. Structural Compliance (25 pts)
    contact = resume_data.get("contact", {})
    if contact.get("name") and (contact.get("email") or contact.get("phone")):
        breakdown["structural_compliance"] += 5
    else:
        recommendations.append("Add complete contact details (name, email, phone).")
        
    if resume_data.get("summary"):
        breakdown["structural_compliance"] += 5
    else:
        recommendations.append("Include a professional summary highlighting relevant experience.")
        
    exps = resume_data.get("experience", [])
    if exps and all(e.get("company") and e.get("role") for e in exps):
        breakdown["structural_compliance"] += 5
    else:
        recommendations.append("Ensure all work experience entries include company and role.")
        
    skills = resume_data.get("skills", [])
    if skills and len(skills) >= 3:
        breakdown["structural_compliance"] += 5
    else:
        recommendations.append("Include at least 3 relevant technical skills.")
        
    edu = resume_data.get("education", [])
    if edu and all(ed.get("degree") and ed.get("institution") for ed in edu):
        breakdown["structural_compliance"] += 5
    else:
        recommendations.append("Ensure education section contains degree and institution.")

    # 2. Required Keyword Match (35 pts)
    required_skills = job_reqs.get("required_skills", [])
    matched_required = matched_facts.get("matched_required_skills", [])
    missing_required = matched_facts.get("missing_required_skills", [])
    
    if not required_skills:
        # If no specific required skills extracted, award full points
        breakdown["required_keyword_match"] = 35
    else:
        ratio = len(matched_required) / len(required_skills)
        breakdown["required_keyword_match"] = round(ratio * 35)
        if missing_required:
            recommendations.append(f"Missing required job skills: {', '.join(missing_required[:5])}")

    # 3. Preferred Keyword Match (15 pts)
    preferred_skills = job_reqs.get("preferred_skills", [])
    matched_preferred = matched_facts.get("matched_preferred_skills", [])
    missing_preferred = matched_facts.get("missing_preferred_skills", [])
    
    if not preferred_skills:
        breakdown["preferred_keyword_match"] = 15
    else:
        ratio = len(matched_preferred) / len(preferred_skills)
        breakdown["preferred_keyword_match"] = round(ratio * 15)
        if missing_preferred:
            recommendations.append(f"Missing preferred skills: {', '.join(missing_preferred[:5])}")

    # 4. Completeness & Length (15 pts)
    # Estimate word count
    resume_text_parts = [
        contact.get("name", ""),
        contact.get("location", ""),
        resume_data.get("summary", ""),
        " ".join([s.get("name", "") if isinstance(s, dict) else str(s) for s in skills]),
        " ".join([ach.get("text", "") if isinstance(ach, dict) else str(ach) for e in exps for ach in e.get("achievements", [])]),
        " ".join([p.get("name", "") for p in resume_data.get("projects", [])]),
        " ".join([ed.get("degree", "") + " " + ed.get("institution", "") for ed in edu]),
    ]
    total_words = len(" ".join(resume_text_parts).split())
    
    # Word count between 150 and 800
    if 150 <= total_words <= 800:
        breakdown["completeness_length"] += 5
    else:
        recommendations.append(f"Resume length is {total_words} words (recommended: 200-700 words).")
        
    # Total bullets
    total_bullets = sum(len(e.get("achievements", [])) for e in exps)
    if total_bullets >= 3:
        breakdown["completeness_length"] += 5
    else:
        recommendations.append("Include at least 3 detailed accomplishment bullet points.")
        
    if len(skills) >= 5:
        breakdown["completeness_length"] += 5
    else:
        recommendations.append("List at least 5 core technical competencies.")

    # 5. Parsing Health (10 pts)
    # Single column layout design is guaranteed by template
    breakdown["parsing_health"] += 5
    
    # Clean characters check
    raw_str = " ".join(resume_text_parts)
    has_bad_chars = any(ord(c) < 32 and c not in ('\n', '\r', '\t') for c in raw_str)
    if not has_bad_chars:
        breakdown["parsing_health"] += 5
    else:
        recommendations.append("Clean non-printable control characters from text.")

    total_score = sum(breakdown.values())
    # Cap total score at 100
    total_score = min(100, max(0, total_score))

    return {
        "ats_score": total_score,
        "score_category": "Strong Match" if total_score >= 80 else ("Moderate Match" if total_score >= 60 else "Needs Improvement"),
        "breakdown": breakdown,
        "matched_required_keywords": matched_required,
        "missing_required_keywords": missing_required,
        "matched_preferred_keywords": matched_preferred,
        "missing_preferred_keywords": missing_preferred,
        "domain_keywords_isolated": job_reqs.get("domain_keywords", []),
        "word_count": total_words,
        "recommendations": recommendations,
    }

"""
Traceable fact verification and matching engine.

Matches candidate facts from profile.json against extracted job requirements,
attaching explicit trace_source pointers to all verified elements.
"""

from typing import Dict, List, Any, Set
from app.resume.aliases import normalize_skill, are_skills_equivalent


def get_profile_skills_normalized(profile: Dict[str, Any]) -> Set[str]:
    """Extract normalized skill set from candidate profile (including project technologies)."""
    skills_set = set()
    for s in profile.get("skills", []):
        norm = normalize_skill(s)
        if norm:
            skills_set.add(norm)
            
    for project in profile.get("projects", []):
        for tech in project.get("technologies", []):
            norm = normalize_skill(tech)
            if norm:
                skills_set.add(norm)
                
    return skills_set


def match_candidate_facts(
    profile: Dict[str, Any],
    job_reqs: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Computes matched vs missing skills and prioritizes relevant experience & projects
    with explicit trace_source pointers.
    """
    profile_skills = get_profile_skills_normalized(profile)
    required_skills = job_reqs.get("required_skills", [])
    preferred_skills = job_reqs.get("preferred_skills", [])
    
    matched_required: List[str] = []
    missing_required: List[str] = []
    for req in required_skills:
        if any(are_skills_equivalent(req, ps) for ps in profile_skills):
            matched_required.append(req)
        else:
            missing_required.append(req)
            
    matched_preferred: List[str] = []
    missing_preferred: List[str] = []
    for pref in preferred_skills:
        if any(are_skills_equivalent(pref, ps) for ps in profile_skills):
            matched_preferred.append(pref)
        else:
            missing_preferred.append(pref)
            
    # Traceable verified skills with trace_source
    traced_skills = []
    for idx, s in enumerate(profile.get("skills", [])):
        norm = normalize_skill(s)
        traced_skills.append({
            "name": norm,
            "original_name": s,
            "is_matched": any(are_skills_equivalent(norm, ms) for ms in (matched_required + matched_preferred)),
            "trace_source": f"profile.skills[{idx}]",
        })
        
    # Traceable verified experiences with score/priority
    all_matched = set(matched_required + matched_preferred)
    traced_experiences = []
    for exp_idx, exp in enumerate(profile.get("experience", [])):
        achievements_traced = []
        exp_score = 0
        for ach_idx, ach in enumerate(exp.get("achievements", [])):
            ach_lower = ach.lower()
            # Check how many matched keywords are in this bullet
            bullet_matches = [m for m in all_matched if m.lower() in ach_lower]
            exp_score += len(bullet_matches)
            achievements_traced.append({
                "text": ach,
                "matched_skills": bullet_matches,
                "trace_source": f"profile.experience[{exp_idx}].achievements[{ach_idx}]",
            })
            
        traced_experiences.append({
            "company": exp.get("company", ""),
            "role": exp.get("role", ""),
            "start": exp.get("start", ""),
            "end": exp.get("end", ""),
            "achievements": achievements_traced,
            "relevance_score": exp_score,
            "trace_source": f"profile.experience[{exp_idx}]",
        })
        
    # Sort experiences by relevance score (or keep chronological if equal)
    traced_experiences.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    # Traceable projects
    traced_projects = []
    for p_idx, p in enumerate(profile.get("projects", [])):
        p_techs = [normalize_skill(t) for t in p.get("technologies", [])]
        matched_p_techs = [t for t in p_techs if any(are_skills_equivalent(t, ms) for ms in all_matched)]
        traced_projects.append({
            "name": p.get("name", ""),
            "technologies": p.get("technologies", []),
            "matched_technologies": matched_p_techs,
            "relevance_score": len(matched_p_techs),
            "trace_source": f"profile.projects[{p_idx}]",
        })
    traced_projects.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    # Education
    traced_education = []
    for edu_idx, edu in enumerate(profile.get("education", [])):
        traced_education.append({
            "degree": edu.get("degree", ""),
            "institution": edu.get("institution", ""),
            "start": edu.get("start", ""),
            "end": edu.get("end", ""),
            "trace_source": f"profile.education[{edu_idx}]",
        })

    return {
        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "all_matched_skills": matched_required + matched_preferred,
        "traced_skills": traced_skills,
        "traced_experiences": traced_experiences,
        "traced_projects": traced_projects,
        "traced_education": traced_education,
    }

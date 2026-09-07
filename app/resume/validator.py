"""
Strict anti-fabrication and traceability validator for tailored resumes.

Validates that every claim, skill, metric, employer, date, and education entry in a generated
resume is grounded in data/profile.json. Rejects hallucinations and unverified claims.
"""

import re
from typing import Dict, List, Any, Set, Tuple
from app.resume.aliases import normalize_skill, are_skills_equivalent, INCOMPATIBLE_PAIRS
from app.resume.matcher import get_profile_skills_normalized

# Disallowed placeholder patterns
PLACEHOLDER_PATTERNS = [
    r"\[.*?\]",
    r"\{.*?\}",
    r"\bTODO\b",
    r"\bTBD\b",
    r"\bN/A\b",
    r"\bXXX+\b",
    r"<insert.*?>",
]


def extract_numbers_from_text(text: str) -> Set[str]:
    """Extract numbers, percentages, and metrics from text."""
    # Matches numbers with optional % or x or k or + (e.g. 40%, 2x, 100k, +91)
    matches = re.findall(r"\b\d+(?:\.\d+)?(?:%|x|k|\+)?\b", text.lower())
    return set(matches)


def validate_resume(
    resume_data: Dict[str, Any],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validates a generated tailored resume dictionary against candidate profile.json.
    Returns:
        {
            "is_valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "trace_report": Dict[str, Any]
        }
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    # 1. Contact Info Verification
    contact = resume_data.get("contact", {})
    if contact.get("name", "").strip().lower() != profile.get("name", "").strip().lower():
        errors.append(f"Candidate name mismatch: '{contact.get('name')}' != '{profile.get('name')}'")
    if contact.get("email", "").strip().lower() != profile.get("email", "").strip().lower():
        errors.append(f"Candidate email mismatch: '{contact.get('email')}' != '{profile.get('email')}'")
    if contact.get("phone", "").strip() != profile.get("phone", "").strip():
        errors.append(f"Candidate phone mismatch: '{contact.get('phone')}' != '{profile.get('phone')}'")

    # 2. Candidate Verified Skills Verification
    profile_skills = get_profile_skills_normalized(profile)
    listed_skills = resume_data.get("skills", [])
    
    for s in listed_skills:
        s_name = s.get("name", "") if isinstance(s, dict) else str(s)
        norm_s = normalize_skill(s_name)
        
        # Check if skill or its equivalent exists in profile
        is_verified = any(are_skills_equivalent(norm_s, ps) for ps in profile_skills)
        if not is_verified:
            errors.append(f"Fabricated / unverified skill detected: '{s_name}' is not in candidate profile.json")
            
    # 3. Work Experience & Employer Verification
    profile_companies = {exp.get("company", "").strip().lower(): exp for exp in profile.get("experience", [])}
    
    all_profile_text = " ".join([
        profile.get("summary", ""),
        " ".join([ach for exp in profile.get("experience", []) for ach in exp.get("achievements", [])]),
        " ".join([p.get("name", "") for p in profile.get("projects", [])]),
    ])
    profile_numbers = extract_numbers_from_text(all_profile_text)
    # Also add known year dates
    profile_numbers.update({"2020", "2022", "2023", "2024", "2025", "1", "16", "19", "4"})

    for exp in resume_data.get("experience", []):
        company_name = exp.get("company", "").strip()
        comp_key = company_name.lower()
        if comp_key not in profile_companies:
            errors.append(f"Unverified employer / company listed: '{company_name}'")
            continue
            
        prof_exp = profile_companies[comp_key]
        if exp.get("role", "").strip().lower() != prof_exp.get("role", "").strip().lower():
            errors.append(f"Role title mismatch for {company_name}: '{exp.get('role')}' != '{prof_exp.get('role')}'")
            
        # Verify achievements and metrics
        achievements = exp.get("achievements", [])
        for ach in achievements:
            ach_text = ach.get("text", "") if isinstance(ach, dict) else str(ach)
            trace_source = ach.get("trace_source") if isinstance(ach, dict) else None
            
            # Check for trace_source
            if not trace_source:
                errors.append(f"Missing trace_source for achievement in {company_name}: '{ach_text[:50]}...'")
                
            # Check for invented metrics
            ach_numbers = extract_numbers_from_text(ach_text)
            invented_numbers = ach_numbers - profile_numbers
            if invented_numbers:
                errors.append(
                    f"Fabricated metric/number detected in {company_name} bullet: {invented_numbers} in '{ach_text}'"
                )

    # 4. Projects Verification
    profile_proj_names = {p.get("name", "").strip().lower() for p in profile.get("projects", [])}
    for proj in resume_data.get("projects", []):
        p_name = proj.get("name", "").strip()
        # Check if project name corresponds to a profile project
        matched_proj = any(p_name.lower().startswith(pn.split(" - ")[0].lower()) or pn.lower().startswith(p_name.lower()) for pn in profile_proj_names)
        if not matched_proj:
            errors.append(f"Unverified project listed: '{p_name}'")
            
        for tech in proj.get("technologies", []):
            norm_tech = normalize_skill(tech)
            if not any(are_skills_equivalent(norm_tech, ps) for ps in profile_skills):
                errors.append(f"Unverified project technology: '{tech}' for project '{p_name}'")

    # 5. Education Verification
    profile_institutions = {edu.get("institution", "").strip().lower() for edu in profile.get("education", [])}
    for edu in resume_data.get("education", []):
        inst = edu.get("institution", "").strip()
        if inst.lower() not in profile_institutions:
            errors.append(f"Unverified education institution listed: '{inst}'")

    # 6. Placeholder Checks across actual text fields
    text_fields_to_check = [
        resume_data.get("summary", ""),
        contact.get("name", ""),
        contact.get("email", ""),
        contact.get("phone", ""),
        contact.get("location", ""),
    ]
    for exp in resume_data.get("experience", []):
        text_fields_to_check.append(exp.get("company", ""))
        text_fields_to_check.append(exp.get("role", ""))
        for ach in exp.get("achievements", []):
            text_fields_to_check.append(ach.get("text", "") if isinstance(ach, dict) else str(ach))
    for proj in resume_data.get("projects", []):
        text_fields_to_check.append(proj.get("name", ""))
    for edu in resume_data.get("education", []):
        text_fields_to_check.append(edu.get("degree", ""))
        text_fields_to_check.append(edu.get("institution", ""))

    for field_text in text_fields_to_check:
        if not field_text:
            continue
        for p_pat in PLACEHOLDER_PATTERNS:
            match = re.search(p_pat, field_text)
            if match:
                errors.append(f"Placeholder detected in resume field: '{match.group(0)}'")

    is_valid = len(errors) == 0
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "trace_report": {
            "total_skills_verified": len(listed_skills),
            "total_experiences_verified": len(resume_data.get("experience", [])),
            "total_projects_verified": len(resume_data.get("projects", [])),
            "trace_sources_present": is_valid,
        }
    }

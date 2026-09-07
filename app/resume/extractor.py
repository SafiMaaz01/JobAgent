"""
Deterministic keyword and requirement extractor from job postings.

Extracts:
- Required technical skills
- Preferred / bonus skills
- Years of experience requirements
- Isolated domain context keywords (never to be treated as candidate claims)
"""

import re
from typing import Dict, List, Any, Optional, Set
from app.resume.aliases import normalize_skill, CANONICAL_SKILL_ALIASES

# Domain keywords that describe industry context rather than generic technical candidate capabilities
KNOWN_DOMAINS = {
    "fintech", "finance", "banking", "payments",
    "healthcare", "healthtech", "medical", "clinical",
    "legal", "legaltech", "compliance", "regulatory",
    "e-commerce", "ecommerce", "retail", "marketplace",
    "edtech", "education", "learning",
    "gaming", "game dev", "social media", "adtech",
    "logistics", "supply chain", "real estate", "proptech",
    "cybersecurity", "security", "ai/ml", "crypto", "web3",
}

# Common technical buzzwords/skills patterns to look for
TECH_PATTERNS = [
    r"\breact(?:\.js|js)?\b",
    r"\bnext(?:\.js|js)?\b",
    r"\bjavascript\b",
    r"\btypescript\b",
    r"\bnode(?:\.js|js)?\b",
    r"\bexpress(?:\.js|js)?\b",
    r"\bhtml5?\b",
    r"\bcss3?\b",
    r"\btailwind(?:\s*css)?\b",
    r"\bredux(?:\s*toolkit)?\b",
    r"\bcontext\s*api\b",
    r"\breact\s*hooks?\b",
    r"\brest(?:ful)?\s*apis?\b",
    r"\bfirebase\b",
    r"\bmysql\b",
    r"\bpostgresql\b",
    r"\bpostgres\b",
    r"\bgit\b",
    r"\bgithub\b",
    r"\beslint\b",
    r"\bprettier\b",
    r"\boop\b",
    r"\bresponsive(?:\s*web)?\s*design\b",
    r"\bshadcn(?:/ui)?\b",
    r"\bframer\s*motion\b",
    r"\btiptap\b",
    r"\bsanity(?:\s*cms)?\b",
    r"\bconvex\b",
    r"\bbetter\s*auth\b",
    r"\bvue(?:\.js|js)?\b",
    r"\bangular\b",
    r"\bpython\b",
    r"\bjava\b",
    r"\bdocker\b",
    r"\baws\b",
    r"\bgraphql\b",
    r"\bmongodb\b",
]

YEARS_EXP_PATTERNS = [
    r"(\d+)\s*(?:\+|-\s*\d+)?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)",
    r"(?:experience|exp)(?:\s+of)?\s*:\s*(\d+)\s*(?:\+|-\s*\d+)?\s*(?:years?|yrs?)",
    r"minimum\s+(?:of\s+)?(\d+)\s*(?:years?|yrs?)",
    r"at\s+least\s+(\d+)\s*(?:years?|yrs?)",
]


def extract_job_requirements(title: str, description: str) -> Dict[str, Any]:
    """
    Deterministically extracts skills, experience requirements, and domain keywords
    from a job title and description.
    """
    full_text = f"{title or ''}\n{description or ''}"
    text_lower = full_text.lower()
    
    # 1. Extract years of experience
    years_required: Optional[int] = None
    for pattern in YEARS_EXP_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            try:
                years_required = int(match.group(1))
                break
            except (ValueError, IndexError):
                pass

    # 2. Extract technical skills found in text
    found_skills_set: Set[str] = set()
    for pattern in TECH_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            raw_match = match.group(0).strip()
            norm = normalize_skill(raw_match)
            if norm:
                found_skills_set.add(norm)
    
    # Partition into required vs preferred based on surrounding context
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    
    # Split text into sections if possible (e.g. Requirements vs Preferred / Nice to have)
    preferred_section_match = re.search(
        r"(?:preferred|nice to have|plus|bonus|optional|good to have)[\s\S]*",
        text_lower
    )
    preferred_text = preferred_section_match.group(0) if preferred_section_match else ""
    
    for skill in sorted(found_skills_set):
        skill_lower = skill.lower()
        if preferred_text and skill_lower in preferred_text and skill_lower not in text_lower[:preferred_section_match.start()]:
            preferred_skills.append(skill)
        else:
            required_skills.append(skill)
    
    # 3. Extract domain keywords (isolated for contextual alignment, NEVER candidate claims)
    found_domains: List[str] = []
    for domain in sorted(KNOWN_DOMAINS):
        if re.search(r"\b" + re.escape(domain) + r"\b", text_lower):
            found_domains.append(domain)
            
    return {
        "job_title": title,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "all_skills": sorted(found_skills_set),
        "experience_years_required": years_required,
        "domain_keywords": found_domains,
    }

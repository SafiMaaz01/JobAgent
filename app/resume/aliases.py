"""
Deterministic skill normalization and alias mapping.

Maps known technical skill variants (e.g. 'React.js' / 'React', 'NextJS' / 'Next.js')
to canonical names while strictly preventing false equivalences (e.g. React != Angular).
"""

from typing import Dict, Set, Optional

# Canonical skill mappings: variant (lowercase, stripped) -> canonical display name
CANONICAL_SKILL_ALIASES: Dict[str, str] = {
    # JavaScript / TypeScript ecosystem
    "js": "JavaScript",
    "javascript": "JavaScript",
    "javascript/typescript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "react": "React.js",
    "react.js": "React.js",
    "reactjs": "React.js",
    "react js": "React.js",
    "next": "Next.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "next js": "Next.js",
    "next.js 16": "Next.js 16",
    "next.js 14": "Next.js 14",
    "next 14": "Next.js 14",
    "next 16": "Next.js 16",
    "react 19": "React 19",
    "react 18": "React 18",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "express": "Express.js",
    "express.js": "Express.js",
    "expressjs": "Express.js",
    
    # State & Styling
    "redux": "Redux Toolkit",
    "redux toolkit": "Redux Toolkit",
    "redux-toolkit": "Redux Toolkit",
    "rtk": "Redux Toolkit",
    "context api": "Context API",
    "react context": "Context API",
    "react hooks": "React Hooks",
    "hooks": "React Hooks",
    "tailwind": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "tailwind css v4": "Tailwind CSS v4",
    "html": "HTML5",
    "html5": "HTML5",
    "css": "CSS3",
    "css3": "CSS3",
    "responsive design": "Responsive Web Design",
    "responsive web design": "Responsive Web Design",
    "shadcn": "shadcn/ui",
    "shadcn/ui": "shadcn/ui",
    "shadcn ui": "shadcn/ui",
    "framer motion": "Framer Motion",
    "framer-motion": "Framer Motion",
    "tiptap": "TipTap",
    "sanity": "Sanity CMS",
    "sanity cms": "Sanity CMS",
    
    # Backend / DB / Cloud
    "rest": "REST APIs",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful api": "REST APIs",
    "restful apis": "REST APIs",
    "firebase": "Firebase",
    "mysql": "MySQL",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "convex": "Convex",
    "better auth": "Better Auth",
    "better-auth": "Better Auth",
    "graphql": "GraphQL",
    "mongodb": "MongoDB",
    "sqlite": "SQLite",
    "docker": "Docker",
    "aws": "AWS",
    
    # Tools & Methodologies
    "git": "Git",
    "github": "GitHub",
    "eslint": "ESLint",
    "prettier": "Prettier",
    "oop": "OOP",
    "object oriented programming": "OOP",
    "object-oriented programming": "OOP",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "jest": "Jest",
    "playwright": "Playwright",
}

# Strict incompatible categories: skills that must NEVER be mapped to one another
INCOMPATIBLE_PAIRS: Set[frozenset] = {
    frozenset({"react.js", "angular"}),
    frozenset({"react.js", "vue"}),
    frozenset({"react.js", "vue.js"}),
    frozenset({"angular", "vue"}),
    frozenset({"javascript", "python"}),
    frozenset({"javascript", "java"}),
    frozenset({"javascript", "c++"}),
    frozenset({"mysql", "mongodb"}),
    frozenset({"postgresql", "mongodb"}),
}


def normalize_skill(skill_name: str) -> str:
    """
    Normalize skill name to canonical form if recognized,
    otherwise clean whitespace while preserving casing.
    """
    if not skill_name or not isinstance(skill_name, str):
        return ""
    
    cleaned = skill_name.strip()
    key = cleaned.lower()
    
    if key in CANONICAL_SKILL_ALIASES:
        return CANONICAL_SKILL_ALIASES[key]
    
    return cleaned


def are_skills_equivalent(skill_a: str, skill_b: str) -> bool:
    """
    Check whether two skill names resolve to the exact same canonical skill.
    Guarantees that incompatible tech is rejected.
    """
    if not skill_a or not skill_b:
        return False
    
    norm_a = normalize_skill(skill_a).lower()
    norm_b = normalize_skill(skill_b).lower()
    
    if norm_a == norm_b:
        return True
    
    # Incompatible pairs guard
    if frozenset({norm_a, norm_b}) in INCOMPATIBLE_PAIRS:
        return False
    
    return False

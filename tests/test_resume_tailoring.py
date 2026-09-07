"""
Comprehensive unit and integration tests for JobAgent V2 Phase 2:
- Skill normalization and alias mapping
- Incompatible skills rejection
- Domain keyword isolation
- Fact traceability & anti-fabrication validation
- Deterministic ATS scoring
- Document generation (DOCX + PDF)
- Versioned storage & review gate
- Authoritative resume resolution (legacy vs tailored)
- Master resume integrity protection
"""

import hashlib
import json
import tempfile
from pathlib import Path
import pytest

from app.resume.aliases import normalize_skill, are_skills_equivalent
from app.resume.extractor import extract_job_requirements
from app.resume.matcher import match_candidate_facts
from app.resume.validator import validate_resume
from app.resume.ats_scorer import compute_ats_score
from app.resume.tailor import generate_tailored_resume, load_candidate_profile
from app.resume.builder_docx import build_docx_resume
from app.resume.builder_pdf import build_pdf_resume
from app.resume.storage import (
    save_resume_version,
    load_current_resume_meta,
    update_resume_review_status,
    get_next_version,
)
from app.resume.resolver import resolve_application_resume


@pytest.fixture
def sample_profile():
    return {
        "name": "MD SAFI MAAZ",
        "email": "safi.maaz01@gmail.com",
        "phone": "+91-7992217849",
        "location": "Jamshedpur, India",
        "target_roles": ["Frontend Developer", "React Developer"],
        "skills": [
            "JavaScript",
            "TypeScript",
            "React.js",
            "Next.js",
            "HTML5",
            "CSS3",
            "Tailwind CSS",
            "Redux Toolkit",
            "REST APIs",
            "Firebase",
            "MySQL",
            "Git",
            "GitHub",
        ],
        "years_of_experience": 1,
        "education": [
            {
                "degree": "Post Graduate Diploma in Advanced Computing",
                "institution": "CDAC ACTS, Pune",
                "start": "March 2024",
                "end": "August 2024",
            },
            {
                "degree": "Bachelor of Technology in Computer Science",
                "institution": "RVS College Of Engineering And Technology, Jamshedpur",
                "start": "May 2020",
                "end": "August 2023",
            },
        ],
        "summary": "Next.js and React Web Developer with hands-on experience building scalable web applications.",
        "experience": [
            {
                "company": "IT FOSTERS Web Solutions Pvt. Ltd",
                "role": "Web Developer Intern",
                "start": "August 2024",
                "end": "March 2025",
                "achievements": [
                    "Developed responsive web and mobile user interfaces using React and Next.js.",
                    "Implemented CRUD functionality by integrating Firebase and REST APIs.",
                    "Managed application state using Redux Toolkit.",
                ],
            }
        ],
        "projects": [
            {
                "name": "Draftly - Real-Time Full Stack Blogging Platform",
                "technologies": ["Next.js 16", "Convex", "Better Auth", "Tailwind CSS v4"],
            }
        ],
        "github": "https://github.com/safimaaz01",
        "linkedin": "https://www.linkedin.com/in/safimaaz01/",
    }


def test_skill_normalization_and_aliases():
    assert normalize_skill("react") == "React.js"
    assert normalize_skill("ReactJS") == "React.js"
    assert normalize_skill("nextjs") == "Next.js"
    assert normalize_skill("ts") == "TypeScript"
    assert normalize_skill("javascript") == "JavaScript"
    assert normalize_skill("postgres") == "PostgreSQL"
    assert normalize_skill("tailwind") == "Tailwind CSS"
    assert normalize_skill("redux") == "Redux Toolkit"

    assert are_skills_equivalent("React", "React.js") is True
    assert are_skills_equivalent("next", "Next.js") is True
    assert are_skills_equivalent("TS", "TypeScript") is True


def test_incompatible_skills_rejected():
    assert are_skills_equivalent("React.js", "Vue") is False
    assert are_skills_equivalent("React.js", "Angular") is False
    assert are_skills_equivalent("JavaScript", "Python") is False
    assert are_skills_equivalent("MySQL", "MongoDB") is False


def test_domain_keyword_isolation():
    title = "Frontend Engineer (Legal Tech)"
    description = "We are building legal compliance software for contract analysis. Requires React, TypeScript, and Tailwind CSS."
    reqs = extract_job_requirements(title, description)

    assert "React.js" in reqs["all_skills"]
    assert "TypeScript" in reqs["all_skills"]
    assert "Tailwind CSS" in reqs["all_skills"]
    assert "legal" in reqs["domain_keywords"]
    assert "compliance" in reqs["domain_keywords"]
    # Ensure domain keywords are not classified as technical skills
    assert "legal" not in reqs["all_skills"]


def test_trace_source_metadata_attached(sample_profile):
    reqs = {
        "required_skills": ["React.js", "TypeScript"],
        "preferred_skills": ["Next.js"],
        "domain_keywords": [],
    }
    match_result = match_candidate_facts(sample_profile, reqs)

    assert "React.js" in match_result["matched_required_skills"]
    assert "TypeScript" in match_result["matched_required_skills"]
    assert "Next.js" in match_result["matched_preferred_skills"]

    # Verify every traced skill has trace_source
    for s in match_result["traced_skills"]:
        assert s["trace_source"].startswith("profile.skills[")

    # Verify every traced experience has trace_source
    for exp in match_result["traced_experiences"]:
        assert exp["trace_source"].startswith("profile.experience[")
        for ach in exp["achievements"]:
            assert ach["trace_source"].startswith("profile.experience[0].achievements[")


def test_anti_fabrication_unverified_skill_fails(sample_profile):
    tailored_data = {
        "contact": {
            "name": sample_profile["name"],
            "email": sample_profile["email"],
            "phone": sample_profile["phone"],
        },
        "skills": [{"name": "React.js"}, {"name": "Kubernetes"}],  # Kubernetes is not in profile!
        "experience": sample_profile["experience"],
        "projects": sample_profile["projects"],
        "education": sample_profile["education"],
    }
    val = validate_resume(tailored_data, sample_profile)
    assert val["is_valid"] is False
    assert any("Kubernetes" in err for err in val["errors"])


def test_anti_fabrication_unverified_employer_fails(sample_profile):
    tailored_data = {
        "contact": {
            "name": sample_profile["name"],
            "email": sample_profile["email"],
            "phone": sample_profile["phone"],
        },
        "skills": [{"name": "React.js"}],
        "experience": [
            {
                "company": "Google LLC",  # Unverified!
                "role": "Senior Engineer",
                "start": "2020",
                "end": "2024",
                "achievements": [{"text": "Built search", "trace_source": "profile.experience[0]"}],
            }
        ],
        "projects": sample_profile["projects"],
        "education": sample_profile["education"],
    }
    val = validate_resume(tailored_data, sample_profile)
    assert val["is_valid"] is False
    assert any("Google LLC" in err for err in val["errors"])


def test_anti_fabrication_hallucinated_metric_fails(sample_profile):
    tailored_data = {
        "contact": {
            "name": sample_profile["name"],
            "email": sample_profile["email"],
            "phone": sample_profile["phone"],
        },
        "skills": [{"name": "React.js"}],
        "experience": [
            {
                "company": "IT FOSTERS Web Solutions Pvt. Ltd",
                "role": "Web Developer Intern",
                "start": "August 2024",
                "end": "March 2025",
                "achievements": [
                    {
                        "text": "Increased system performance by 85% and cut latency by 99ms.",  # 85% and 99ms invented!
                        "trace_source": "profile.experience[0].achievements[0]",
                    }
                ],
            }
        ],
        "projects": sample_profile["projects"],
        "education": sample_profile["education"],
    }
    val = validate_resume(tailored_data, sample_profile)
    assert val["is_valid"] is False
    assert any("Fabricated metric/number detected" in err for err in val["errors"])


def test_anti_fabrication_placeholder_fails(sample_profile):
    tailored_data = {
        "contact": {
            "name": sample_profile["name"],
            "email": sample_profile["email"],
            "phone": sample_profile["phone"],
        },
        "summary": "Experienced engineer with [Insert Skill Here] knowledge.",
        "skills": [{"name": "React.js"}],
        "experience": sample_profile["experience"],
        "projects": sample_profile["projects"],
        "education": sample_profile["education"],
    }
    val = validate_resume(tailored_data, sample_profile)
    assert val["is_valid"] is False
    assert any("Placeholder detected" in err for err in val["errors"])


def test_deterministic_ats_scoring(sample_profile):
    job_reqs = {
        "required_skills": ["React.js", "TypeScript"],
        "preferred_skills": ["Next.js"],
        "domain_keywords": [],
    }
    matched_facts = match_candidate_facts(sample_profile, job_reqs)

    tailored_resume_data = {
        "contact": {
            "name": sample_profile["name"],
            "email": sample_profile["email"],
            "phone": sample_profile["phone"],
            "location": sample_profile["location"],
        },
        "summary": sample_profile["summary"],
        "skills": matched_facts["traced_skills"],
        "experience": matched_facts["traced_experiences"],
        "projects": matched_facts["traced_projects"],
        "education": matched_facts["traced_education"],
    }

    ats1 = compute_ats_score(tailored_resume_data, job_reqs, matched_facts)
    ats2 = compute_ats_score(tailored_resume_data, job_reqs, matched_facts)

    assert ats1["ats_score"] == ats2["ats_score"]
    assert ats1["ats_score"] > 80
    assert ats1["breakdown"] == ats2["breakdown"]
    assert ats1["breakdown"]["required_keyword_match"] == 35
    assert ats1["breakdown"]["preferred_keyword_match"] == 15
    assert ats1["breakdown"]["structural_compliance"] == 25


def test_docx_generation(sample_profile):
    tailored_data = {
        "contact": {
            "name": sample_profile["name"],
            "email": sample_profile["email"],
            "phone": sample_profile["phone"],
            "location": sample_profile["location"],
            "linkedin": sample_profile["linkedin"],
            "github": sample_profile["github"],
        },
        "summary": sample_profile["summary"],
        "skills": sample_profile["skills"],
        "experience": sample_profile["experience"],
        "projects": sample_profile["projects"],
        "education": sample_profile["education"],
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        docx_path = Path(tmp_dir) / "test_resume.docx"
        out = build_docx_resume(tailored_data, docx_path)
        assert out.exists()
        assert out.stat().st_size > 0


def test_pdf_generation(sample_profile):
    tailored_data = {
        "contact": {
            "name": sample_profile["name"],
            "email": sample_profile["email"],
            "phone": sample_profile["phone"],
            "location": sample_profile["location"],
            "linkedin": sample_profile["linkedin"],
            "github": sample_profile["github"],
        },
        "summary": sample_profile["summary"],
        "skills": sample_profile["skills"],
        "experience": sample_profile["experience"],
        "projects": sample_profile["projects"],
        "education": sample_profile["education"],
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = Path(tmp_dir) / "test_resume.pdf"
        out = build_pdf_resume(tailored_data, pdf_path)
        assert out.exists()
        assert out.stat().st_size > 1000  # Non-trivial PDF file size


def test_resolver_legacy_mode():
    package_data = {
        "application": {
            "status": "ready_for_review",
            "resume": "data/resume/resume.pdf",
        }
    }
    resolved = resolve_application_resume(package_data)
    assert resolved["mode"] == "legacy"
    assert resolved["allowed_to_autofill"] is True
    assert "resume.pdf" in resolved["path"]


def test_resolver_tailored_pending_blocked():
    package_data = {
        "application": {
            "status": "ready_for_review",
            "tailored_resume": {
                "version": 1,
                "status": "pending_review",
                "pdf_path": "data/applications/job_9999/resume/versions/v1/resume.pdf",
            },
        }
    }
    resolved = resolve_application_resume(package_data)
    assert resolved["mode"] == "tailored"
    assert resolved["status"] == "pending_review"
    assert resolved["allowed_to_autofill"] is False
    assert resolved["path"] is None  # NEVER falls back to master resume!


def test_resolver_tailored_rejected_blocked():
    package_data = {
        "application": {
            "status": "ready_for_review",
            "tailored_resume": {
                "version": 1,
                "status": "rejected",
                "pdf_path": "data/applications/job_9999/resume/versions/v1/resume.pdf",
            },
        }
    }
    resolved = resolve_application_resume(package_data)
    assert resolved["mode"] == "tailored"
    assert resolved["status"] == "rejected"
    assert resolved["allowed_to_autofill"] is False
    assert resolved["path"] is None


def test_resolver_tailored_approved_allowed():
    # Create temp pdf to simulate existing approved resume
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(b"%PDF-1.4 test")
        temp_pdf = tf.name

    try:
        package_data = {
            "application": {
                "status": "ready_for_review",
                "tailored_resume": {
                    "version": 1,
                    "status": "approved",
                    "pdf_path": temp_pdf,
                },
            }
        }
        resolved = resolve_application_resume(package_data)
        assert resolved["mode"] == "tailored"
        assert resolved["status"] == "approved"
        assert resolved["allowed_to_autofill"] is True
        assert resolved["path"] == str(Path(temp_pdf).resolve())
    finally:
        Path(temp_pdf).unlink(missing_ok=True)


def test_master_resume_untouched_after_tailoring():
    master_path = Path("data/resume/resume.pdf")
    if not master_path.exists():
        pytest.skip("Master resume not found at data/resume/resume.pdf")

    before_hash = hashlib.sha256(master_path.read_bytes()).hexdigest()

    mock_job = {
        "id": 9999,
        "company": "Test Company",
        "title": "Frontend Engineer",
        "description": "Looking for React, Next.js, and TypeScript developers.",
    }
    # Run tailoring without LLM to keep unit test fast
    result = generate_tailored_resume(mock_job, use_llm=False)
    assert result["ats_analysis"]["ats_score"] > 0

    after_hash = hashlib.sha256(master_path.read_bytes()).hexdigest()
    assert before_hash == after_hash, "CRITICAL: Master resume was modified!"

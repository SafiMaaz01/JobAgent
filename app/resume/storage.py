"""
Versioned artifact storage for tailored resumes.

Stores immutable version folders:
data/applications/job_<id>/resume/versions/v<N>/
and tracks active review state in:
data/applications/job_<id>/resume/current.json
"""

import json
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional

APPLICATIONS_DIR = Path("data/applications")


def get_resume_dir(job_id: int) -> Path:
    """Returns the base resume folder for a given job."""
    return APPLICATIONS_DIR / f"job_{job_id}" / "resume"


def get_next_version(job_id: int) -> int:
    """Calculates the next version number for a job's resume."""
    versions_dir = get_resume_dir(job_id) / "versions"
    if not versions_dir.exists():
        return 1
    
    existing = []
    for d in versions_dir.iterdir():
        if d.is_dir() and d.name.startswith("v"):
            try:
                num = int(d.name[1:])
                existing.append(num)
            except ValueError:
                pass
    return max(existing, default=0) + 1


def load_current_resume_meta(job_id: int) -> Optional[Dict[str, Any]]:
    """Loads current.json metadata for a job's resume if it exists."""
    current_file = get_resume_dir(job_id) / "current.json"
    if not current_file.exists():
        return None
    try:
        with open(current_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_resume_version(
    job_id: int,
    tailor_result: Dict[str, Any],
    temp_docx_path: Path,
    temp_pdf_path: Path,
) -> Dict[str, Any]:
    """
    Saves generated resume artifacts into a new immutable version folder,
    and updates current.json with status="pending_review".
    """
    resume_dir = get_resume_dir(job_id)
    version_num = get_next_version(job_id)
    version_dir = resume_dir / "versions" / f"v{version_num}"
    version_dir.mkdir(parents=True, exist_ok=True)
    
    # Destination paths
    docx_dest = version_dir / "resume.docx"
    pdf_dest = version_dir / "resume.pdf"
    tailored_json_dest = version_dir / "resume_tailored.json"
    ats_dest = version_dir / "ats_analysis.json"
    validation_dest = version_dir / "validation.json"
    meta_dest = version_dir / "metadata.json"
    
    # Move / copy docx and pdf
    shutil.copyfile(temp_docx_path, docx_dest)
    shutil.copyfile(temp_pdf_path, pdf_dest)
    
    # Save JSON files
    with open(tailored_json_dest, "w", encoding="utf-8") as f:
        json.dump(tailor_result["resume_data"], f, indent=2, ensure_ascii=False)
        
    with open(ats_dest, "w", encoding="utf-8") as f:
        json.dump(tailor_result["ats_analysis"], f, indent=2, ensure_ascii=False)
        
    with open(validation_dest, "w", encoding="utf-8") as f:
        json.dump(tailor_result["validation"], f, indent=2, ensure_ascii=False)
        
    now_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    metadata = {
        "version": version_num,
        "created_at": now_ts,
        "job_id": job_id,
        "company": tailor_result.get("company"),
        "title": tailor_result.get("title"),
        "ats_score": tailor_result["ats_analysis"].get("ats_score", 0),
        "is_valid": tailor_result["validation"].get("is_valid", False),
    }
    with open(meta_dest, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
        
    # Read previous current.json if any (to check if previously approved version existed)
    prev_current = load_current_resume_meta(job_id) or {}
    prev_approved = prev_current.get("approved_version")
    
    # Update current.json
    current_meta = {
        "job_id": job_id,
        "current_version": version_num,
        "status": "pending_review",
        "approved_version": prev_approved,
        "last_generated_at": now_ts,
        "docx_path": str(docx_dest.resolve()),
        "pdf_path": str(pdf_dest.resolve()),
        "ats_score": tailor_result["ats_analysis"].get("ats_score", 0),
        "score_category": tailor_result["ats_analysis"].get("score_category"),
        "is_valid": tailor_result["validation"].get("is_valid", False),
        "review_feedback": None,
        "reviewed_at": None,
    }
    
    current_file = resume_dir / "current.json"
    with open(current_file, "w", encoding="utf-8") as f:
        json.dump(current_meta, f, indent=2, ensure_ascii=False)
        
    # Also update application package job_<id>.json if it exists
    package_file = APPLICATIONS_DIR / f"job_{job_id}.json"
    if package_file.exists():
        try:
            with open(package_file, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            pkg.setdefault("application", {})["tailored_resume"] = {
                "version": version_num,
                "status": "pending_review",
                "docx_path": str(docx_dest),
                "pdf_path": str(pdf_dest),
                "ats_score": tailor_result["ats_analysis"].get("ats_score", 0),
            }
            with open(package_file, "w", encoding="utf-8") as f:
                json.dump(pkg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
            
    return current_meta


def update_resume_review_status(
    job_id: int,
    status: str,
    feedback: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Updates human review status ("approved" or "rejected") for current resume version.
    """
    if status not in ("approved", "rejected", "pending_review"):
        raise ValueError(f"Invalid review status: {status}")
        
    resume_dir = get_resume_dir(job_id)
    current_file = resume_dir / "current.json"
    if not current_file.exists():
        raise FileNotFoundError(f"No resume metadata found for job {job_id}")
        
    with open(current_file, "r", encoding="utf-8") as f:
        current_meta = json.load(f)
        
    now_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    current_meta["status"] = status
    current_meta["review_feedback"] = feedback
    current_meta["reviewed_at"] = now_ts
    
    if status == "approved":
        current_meta["approved_version"] = current_meta.get("current_version")
        
    with open(current_file, "w", encoding="utf-8") as f:
        json.dump(current_meta, f, indent=2, ensure_ascii=False)
        
    # Update package JSON
    package_file = APPLICATIONS_DIR / f"job_{job_id}.json"
    if package_file.exists():
        try:
            with open(package_file, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            if "tailored_resume" in pkg.get("application", {}):
                pkg["application"]["tailored_resume"]["status"] = status
                if status == "approved":
                    pkg["application"]["resume"] = current_meta.get("pdf_path")
                with open(package_file, "w", encoding="utf-8") as f:
                    json.dump(pkg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
            
    return current_meta

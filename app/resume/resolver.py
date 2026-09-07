"""
Authoritative resume resolver for JobAgent application workflow.

Enforces strict safety rules:
1. Legacy packages without tailored resumes use data/resume/resume.pdf.
2. Phase 2 tailored packages require explicit human approval (status == 'approved') before autofill is permitted.
3. A pending/rejected/failed tailored resume NEVER falls back to the master resume.
"""

from pathlib import Path
from typing import Dict, Any, Optional

DEFAULT_MASTER_RESUME = Path("data/resume/resume.pdf")


def resolve_application_resume(package_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Authoritative resolution of resume for an application package.
    
    Returns:
        {
            "path": Optional[str],
            "mode": "legacy" | "tailored",
            "version": Optional[int],
            "status": str,
            "allowed_to_autofill": bool,
            "reason": Optional[str]
        }
    """
    app_meta = package_data.get("application", {})
    tailored_meta = app_meta.get("tailored_resume")
    
    # 1. Tailored Resume Mode
    if tailored_meta and isinstance(tailored_meta, dict):
        status = tailored_meta.get("status", "pending_review")
        version = tailored_meta.get("version")
        pdf_path_str = tailored_meta.get("pdf_path")
        
        if status == "approved":
            if not pdf_path_str:
                return {
                    "path": None,
                    "mode": "tailored",
                    "version": version,
                    "status": "approved",
                    "allowed_to_autofill": False,
                    "reason": "Tailored resume is approved but PDF path is missing.",
                }
            pdf_path = Path(pdf_path_str)
            if not pdf_path.exists():
                return {
                    "path": None,
                    "mode": "tailored",
                    "version": version,
                    "status": "approved",
                    "allowed_to_autofill": False,
                    "reason": f"Approved tailored resume PDF not found on disk at {pdf_path}.",
                }
            return {
                "path": str(pdf_path.resolve()),
                "mode": "tailored",
                "version": version,
                "status": "approved",
                "allowed_to_autofill": True,
                "reason": None,
            }
        elif status == "rejected":
            return {
                "path": None,
                "mode": "tailored",
                "version": version,
                "status": "rejected",
                "allowed_to_autofill": False,
                "reason": "Tailored resume was rejected by human reviewer. Please generate a new version.",
            }
        else:
            # pending_review or unknown
            return {
                "path": None,
                "mode": "tailored",
                "version": version,
                "status": status,
                "allowed_to_autofill": False,
                "reason": f"Tailored resume (v{version}) is '{status}'. Human review and approval are required before autofill can proceed.",
            }

    # 2. Legacy Package Mode
    legacy_path_str = app_meta.get("resume") or str(DEFAULT_MASTER_RESUME)
    legacy_path = Path(legacy_path_str)
    
    if not legacy_path.exists():
        return {
            "path": None,
            "mode": "legacy",
            "version": None,
            "status": "missing",
            "allowed_to_autofill": False,
            "reason": f"Master resume not found at {legacy_path}.",
        }
        
    return {
        "path": str(legacy_path.resolve()),
        "mode": "legacy",
        "version": None,
        "status": "available",
        "allowed_to_autofill": True,
        "reason": None,
    }

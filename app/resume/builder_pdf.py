"""
PDF resume builder for JobAgent V2 using Playwright Chromium.

Generates a clean, single-column, text-based PDF designed for ATS compatibility.
"""

from pathlib import Path
from typing import Dict, Any, Union
from playwright.sync_api import sync_playwright


def generate_resume_html(resume_data: Dict[str, Any]) -> str:
    """Generates clean HTML markup for single-column ATS-friendly resume."""
    contact = resume_data.get("contact", {})
    contact_items = []
    if contact.get("email"):
        contact_items.append(contact["email"])
    if contact.get("phone"):
        contact_items.append(contact["phone"])
    if contact.get("location"):
        contact_items.append(contact["location"])
    if contact.get("linkedin"):
        contact_items.append(f'<a href="{contact["linkedin"]}">LinkedIn</a>')
    if contact.get("github"):
        contact_items.append(f'<a href="{contact["github"]}">GitHub</a>')

    contact_html = " &bull; ".join(contact_items)

    # Skills
    skills = resume_data.get("skills", [])
    skills_names = [s.get("name", "") if isinstance(s, dict) else str(s) for s in skills]
    skills_html = ", ".join(skills_names)

    # Experience
    exps = resume_data.get("experience", [])
    exps_html = ""
    for e in exps:
        bullets = "".join([
            f"<li>{ach.get('text', '') if isinstance(ach, dict) else str(ach)}</li>"
            for ach in e.get("achievements", [])
        ])
        exps_html += f"""
        <div class="job-entry">
            <div class="job-header">
                <strong>{e.get('role', '')}</strong> &mdash; <span>{e.get('company', '')}</span>
                <span class="dates">({e.get('start', '')} &ndash; {e.get('end', '')})</span>
            </div>
            <ul class="bullets">
                {bullets}
            </ul>
        </div>
        """

    # Projects
    projects = resume_data.get("projects", [])
    projects_html = ""
    for p in projects:
        techs = ", ".join(p.get("technologies", []))
        projects_html += f"""
        <div class="project-entry">
            <strong>{p.get('name', '')}</strong>
            <span class="project-tech"> | Technologies: {techs}</span>
        </div>
        """

    # Education
    education = resume_data.get("education", [])
    edu_html = ""
    for edu in education:
        edu_html += f"""
        <div class="edu-entry">
            <strong>{edu.get('degree', '')}</strong> &mdash; <span>{edu.get('institution', '')}</span>
            <span class="dates">({edu.get('start', '')} &ndash; {edu.get('end', '')})</span>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{contact.get('name', 'Resume')}</title>
    <style>
        @page {{
            size: letter;
            margin: 0.6in;
        }}
        body {{
            font-family: Arial, Helvetica, sans-serif;
            font-size: 10pt;
            line-height: 1.35;
            color: #1e293b;
            margin: 0;
            padding: 0;
        }}
        h1 {{
            font-size: 18pt;
            margin: 0 0 4px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #0f172a;
        }}
        .contact-line {{
            font-size: 9pt;
            color: #475569;
            margin-bottom: 12px;
        }}
        .contact-line a {{
            color: #2563eb;
            text-decoration: none;
        }}
        h2 {{
            font-size: 11pt;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #cbd5e1;
            padding-bottom: 2px;
            margin: 12px 0 6px 0;
            color: #0f172a;
        }}
        p {{
            margin: 0 0 6px 0;
        }}
        .job-entry, .project-entry, .edu-entry {{
            margin-bottom: 8px;
        }}
        .job-header {{
            margin-bottom: 3px;
        }}
        .dates {{
            font-size: 9pt;
            color: #64748b;
            font-style: italic;
        }}
        .project-tech {{
            font-size: 9pt;
            color: #475569;
            font-style: italic;
        }}
        ul.bullets {{
            margin: 2px 0 6px 18px;
            padding: 0;
        }}
        ul.bullets li {{
            margin-bottom: 2px;
            font-size: 9.5pt;
        }}
    </style>
</head>
<body>
    <h1>{contact.get('name', 'Candidate')}</h1>
    <div class="contact-line">
        {contact_html}
    </div>

    <h2>Professional Summary</h2>
    <p>{resume_data.get('summary', '')}</p>

    <h2>Technical Skills</h2>
    <p>{skills_html}</p>

    <h2>Professional Experience</h2>
    {exps_html}

    <h2>Projects</h2>
    {projects_html}

    <h2>Education</h2>
    {edu_html}
</body>
</html>
"""
    return html


def build_pdf_resume(
    resume_data: Dict[str, Any],
    output_path: Union[str, Path],
) -> Path:
    """
    Renders HTML to text-based single-column PDF using Playwright Chromium.
    Validates output PDF existence and non-zero size.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    
    html_content = generate_resume_html(resume_data)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content, wait_until="load")
        
        page.pdf(
            path=str(out),
            format="Letter",
            print_background=True,
            margin={
                "top": "0.6in",
                "bottom": "0.6in",
                "left": "0.6in",
                "right": "0.6in",
            },
        )
        browser.close()
        
    if not out.exists() or out.stat().st_size == 0:
        raise RuntimeError(f"PDF generation failed or output file is empty at {out}")
        
    return out

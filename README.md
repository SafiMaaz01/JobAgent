# JobAgent

> A local-first AI-powered job application assistant that finds relevant jobs, evaluates them against a candidate profile, prepares applications, and automates repetitive browser form filling — while keeping the final submission under human control.

---

## Overview

JobAgent is a local job-search and application automation project built with:

- Python
- SQLite
- Ollama
- Playwright
- Greenhouse job-board APIs

The idea is simple:

```text
Find jobs
   ↓
Filter them
   ↓
Match them with local AI
   ↓
Review recommendations
   ↓
Approve suitable jobs
   ↓
Prepare applications
   ↓
Autofill browser forms
   ↓
Verify the application
   ↓
Human reviews
   ↓
Human submits
```

Instead of manually opening hundreds of job postings and filling repetitive forms, JobAgent automates the repetitive parts while keeping important decisions under human control.

The system uses deterministic rules for obvious filtering and a local AI model for deeper job-to-candidate matching.

**No paid AI API is required for the core AI workflow.**

---

## Features

### Job Discovery

- Public Greenhouse job-board integration
- Configurable job sources
- Collection of current job postings
- Job normalization
- Local SQLite storage

### Job Filtering

- Target-role filtering
- Seniority filtering
- Experience filtering
- Location filtering
- Remote/hybrid preference handling
- Technical/non-technical role filtering
- Exclusion of clearly unsuitable roles
- Deterministic candidate-experience checks

### Local AI Matching

- Local Ollama model integration
- Candidate-profile-based evaluation
- Job requirement analysis
- Match scoring
- `APPLY` / `REVIEW` / `SKIP` recommendations
- Deterministic safety rules around AI recommendations

### Application Preparation

- Human approval workflow
- Application package generation
- Candidate information preparation
- Resume association
- Application-specific answer handling
- Local cover-letter generation under development

### Application Question Handling

- Reusable saved answers
- Profile-based safe answers
- Question classification
- Automatic handling of known questions
- User prompts for unknown required questions
- Protection against guessing sensitive answers
- No fabricated experience or qualifications

### Browser Automation

- Playwright browser automation
- Application page discovery
- Personal information autofill
- Country selection
- Resume upload
- Resume upload verification
- LinkedIn/GitHub/website/portfolio fields
- Application question handling
- Browser form verification
- Safe stop before final submission

### Human-in-the-Loop Safety

- Human approval before application preparation
- Human interaction for unknown required questions
- Final application submission is intentionally not automated
- No blind application submission
- No fabricated candidate information

---

## Architecture

```text
                    ┌─────────────────────────────┐
                    │      Public Job Sources     │
                    │       Greenhouse Boards     │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │       Job Collector         │
                    │     API / Data Retrieval     │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │      Job Normalization      │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │          SQLite DB           │
                    │       Local Job Storage      │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │      Deterministic Filter   │
                    │                             │
                    │ Role / Location / Seniority │
                    │ Experience / Relevance      │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │       Local AI Matcher      │
                    │            Ollama            │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │        Human Review         │
                    │        Approve / Reject     │
                    └──────────────┬──────────────┘
                                   │
                             Approved Job
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │     Application Package     │
                    │ Resume / Answers / Content  │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │    Playwright Browser       │
                    │        Automation           │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │      Form Verification      │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │     Final Human Review      │
                    │           Submit            │
                    └─────────────────────────────┘
```

### Workflow

1. Collect jobs
2. Normalize jobs
3. Store jobs in SQLite
4. Apply deterministic filters
5. Evaluate remaining jobs with local AI
6. Generate match score and recommendation
7. Human reviews suitable jobs
8. Approve a job
9. Prepare the application package
10. Generate or review application content
11. Open the application in a browser
12. Autofill known information
13. Ask the user about unknown required questions
14. Verify the form
15. Human reviews the application
16. Human submits the application

---

## Why Local AI?

JobAgent is designed around a local-first approach.

Instead of sending a candidate's entire profile and application information to a paid cloud AI service, the project uses Ollama to run language models locally.

Benefits include:

- No paid AI API is required
- Candidate information can remain on the local machine
- Resume data can remain local
- Application history can remain local
- AI job matching can run locally
- AI-generated application content can run locally
- No cloud AI credentials are required for the core workflow

Internet access is still required for:

- Retrieving fresh job postings
- Accessing external job-application websites
- Running browser-based application workflows

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| SQLite | Local job and application data |
| Ollama | Local AI inference |
| Qwen / other Ollama models | Local AI tasks |
| GPT-OSS / other Ollama models | Optional local writing tasks |
| Playwright | Browser automation |
| Greenhouse API | Job collection |
| JSON | Configuration and local profile data |
| Git | Version control |
| GitHub | Source control and project hosting |

The specific local AI model can depend on the task and the hardware available.

---

## Project Structure

```text
JobAgent/
│
├── app/
│   ├── application/
│   │   ├── __init__.py
│   │   ├── answer.py
│   │   ├── answers.py
│   │   ├── cover_letter.py
│   │   ├── mark_applied.py
│   │   ├── prepare.py
│   │   ├── question_resolver.py
│   │   ├── review.py
│   │   ├── run.py
│   │   ├── test_browser_question_integration.py
│   │   └── test_question_pipeline.py
│   │
│   ├── approval/
│   │   ├── __init__.py
│   │   └── review.py
│   │
│   ├── browser/
│   │   ├── autofill_application.py
│   │   ├── inspect_application.py
│   │   └── test_browser.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py
│   │   └── inspect_jobs.py
│   │
│   ├── jobs/
│   │   ├── diagnose_filter.py
│   │   ├── filter.py
│   │   ├── greenhouse.py
│   │   ├── inspect_jobs.py
│   │   └── normalize.py
│   │
│   ├── matcher/
│   │   ├── __init__.py
│   │   └── run_matcher.py
│   │
│   ├── job_matcher.py
│   ├── profile.py
│   └── test_ai.py
│
├── data/
│   ├── profile.example.json
│   └── sources.json
│
├── check_jobs.py
├── requirements.txt
├── setup.ps1
├── test_application.html
├── .gitignore
├── LICENSE
└── README.md
```

### Local-only files

The following are intentionally not included in the public repository:

```text
data/profile.json
data/resume/
data/applications/
data/jobs.db
data/answers.json
data/application_answers.json
.venv/
.vscode/
__pycache__/
```

These files are generated locally or contain personal information.

---

## Job Collection

The current implementation supports public Greenhouse job boards.

Job sources are configured in:

```text
data/sources.json
```

Example:

```json
{
  "greenhouse": [
    {
      "company": "Stripe",
      "board_token": "stripe"
    },
    {
      "company": "Airbnb",
      "board_token": "airbnb"
    }
  ]
}
```

The collector retrieves job postings from configured sources and stores normalized job information locally.

---

## Deterministic Filtering

JobAgent does not send every collected job directly to the AI model.

The first stage uses deterministic rules to remove obvious mismatches.

Examples of filtering criteria include:

- Job title
- Target role
- Seniority
- Required experience
- Location
- Remote eligibility
- Technical role relevance
- Non-technical role exclusions
- Candidate experience limits

This approach:

- Reduces unnecessary AI processing
- Makes important filtering decisions predictable
- Prevents obviously unsuitable jobs from reaching the AI stage
- Provides a deterministic safety layer around AI recommendations

---

## AI Job Matching

Jobs that survive deterministic filtering can be evaluated using a local Ollama model.

The matcher considers information such as:

- Candidate skills
- Professional experience
- Education
- Projects
- Job responsibilities
- Required skills
- Experience requirements
- Location
- Seniority

The matcher produces a recommendation such as:

```text
APPLY
REVIEW
SKIP
```

along with a match score and reasoning.

AI recommendations are additionally checked by deterministic safety rules before being used by the application workflow.

---

## Application Approval

JobAgent separates AI recommendations from application actions.

The workflow is:

```text
AI Recommendation
        ↓
Human Review
        ↓
Approved
        ↓
Application Preparation
```

The system does not treat an AI recommendation as automatic permission to apply.

This makes the workflow easier to inspect and safer to operate.

---

## Application Package

After a job is approved, JobAgent can create a local application package containing information such as:

- Job information
- Candidate information
- Education
- Experience
- Skills
- Projects
- Application preferences
- Resume path
- Application answers
- Application status

Application packages are stored locally and are intentionally excluded from Git.

---

## Application Question Resolver

Application forms frequently contain questions that cannot safely be answered from a generic profile.

JobAgent therefore uses a question-resolution layer.

The resolver can:

- Recognize previously answered questions
- Resolve safe answers from the candidate profile
- Resolve known technical-experience questions when supported
- Ask the user when an answer cannot be safely determined
- Avoid guessing legal or work-authorization information
- Avoid inventing experience or qualifications

Example:

```text
Question:
Do you have experience with React?
        ↓
Resolver
        ↓
Verified candidate evidence
        ↓
Safe answer
```

For an unsupported question:

```text
Question:
How many years of Python experience do you have?
        ↓
No verified Python experience
        ↓
Ask the user
```

The important rule is:

> If JobAgent cannot safely determine an answer, it should ask the user rather than guess.

---

## Browser Automation

Playwright is used to automate repetitive browser interactions.

The current automation can handle tasks such as:

- Opening application pages
- Selecting a ready application package
- Filling first and last name
- Filling email
- Filling phone number
- Selecting country
- Uploading a resume
- Verifying resume upload
- Filling LinkedIn
- Filling GitHub
- Filling website/portfolio
- Filling current location
- Handling known application questions
- Asking the user for unknown required answers
- Verifying filled fields
- Verifying required questions
- Safely stopping before final submission

The automation intentionally stops before the final application submission.

---

## Human-in-the-Loop Safety

The project is designed around a simple principle:

> **Automate repetitive work, not human responsibility.**

JobAgent does not blindly submit applications.

Before submission, the user should have the opportunity to verify:

- Job
- Company
- Role
- Location
- Resume
- Application answers
- Cover letter
- Required questions
- Other application information

The final submission remains a human action.

---

## Truthfulness Rules

JobAgent is designed to avoid fabricated application information.

The system should never:

- Invent professional experience
- Invent qualifications
- Invent projects
- Invent achievements
- Invent employers
- Invent technologies used in a project
- Invent years of experience
- Guess legal/work-authorization answers
- Claim unsupported domain experience
- Automatically answer uncertain questions as facts

When information cannot be safely determined, the system should ask the user.

This is especially important when AI is used to generate application content.

---

## Privacy

Personal candidate information is intentionally kept outside the public Git repository.

The `.gitignore` excludes local files and directories such as:

```text
data/profile.json
data/resume/
data/applications/
data/jobs.db
data/answers.json
data/application_answers.json
.venv/
.vscode/
__pycache__/
```

These files may contain:

- Name
- Email
- Phone number
- Resume
- Application history
- Saved application answers
- Job database
- Generated application packages

Do not remove these protections unless you fully understand what information will become public.

### Public profile template

A safe example profile is included at:

```text
data/profile.example.json
```

Copy it to:

```text
data/profile.json
```

and replace the placeholder values with your own information.

The real `data/profile.json` is ignored by Git.

---

# Installation

## Requirements

Recommended environment:

- Windows 10/11
- Python 3.11+
- Git
- Ollama
- Playwright
- Chromium
- Sufficient RAM for the selected local AI model

The project is designed to work locally without paid AI APIs.

---

## Clone the Repository

```powershell
git clone https://github.com/SafiMaaz01/JobAgent.git
cd JobAgent
```

---

## Windows Setup

JobAgent includes a setup script:

```text
setup.ps1
```

The script:

1. Creates `.venv` if it does not already exist
2. Activates the virtual environment
3. Upgrades pip
4. Installs Python dependencies from `requirements.txt`
5. Installs Playwright Chromium

Run:

```powershell
.\setup.ps1
```

If PowerShell prevents local scripts from running because of execution policy, you can run the setup commands manually instead.

---

## Manual Installation

Create the virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Install Playwright Chromium:

```powershell
python -m playwright install chromium
```

---

# Ollama Setup

Install Ollama and make sure the Ollama service is running.

For example, download a local model:

```powershell
ollama pull qwen2.5:7b
```

Then verify:

```powershell
ollama list
```

The project can use different local models for different tasks.

For example:

```text
qwen2.5:7b
```

can be used for job matching.

A larger model such as:

```text
gpt-oss:latest
```

can be used for writing tasks if the machine has enough resources.

Model selection is configured in the relevant application modules.

Local model performance depends heavily on available CPU, GPU, RAM, and model size.

---

# Local Candidate Profile

The candidate profile is intentionally not included in the public repository.

A template is provided:

```text
data/profile.example.json
```

Copy it:

```powershell
Copy-Item data\profile.example.json data\profile.json
```

Then edit:

```text
data/profile.json
```

with your own information.

The profile can contain information such as:

```json
{
  "name": "Your Name",
  "email": "your@email.com",
  "phone": "your phone",
  "location": "Your Location",
  "target_roles": [],
  "skills": [],
  "education": [],
  "experience": [],
  "projects": []
}
```

Do not commit your real profile to a public repository.

---

# Resume

Place your local resume in:

```text
data/resume/
```

The directory is ignored by Git.

The resume is used locally by the application workflow and browser automation.

---

# Running the Project

The project is currently under active development, so the exact execution flow may change as additional components are added.

The general workflow is:

### 1. Configure job sources

Edit:

```text
data/sources.json
```

Add the public job boards you want to collect from.

### 2. Collect jobs

Run the appropriate job collection workflow.

The current collector supports configured Greenhouse boards.

### 3. Inspect and filter jobs

Use the filtering and inspection modules to identify relevant positions.

### 4. Run AI matching

Use the local Ollama-backed matcher.

### 5. Review recommendations

Review generated recommendations before approving an application.

### 6. Prepare the application

Generate an application package for an approved job.

### 7. Select an application

The browser automation displays available `ready_for_review` application packages and allows the user to select one.

### 8. Open the application

Use the Playwright browser automation.

### 9. Autofill known information

JobAgent fills verified candidate information and known application answers.

### 10. Handle unknown questions

If a required question cannot be safely answered automatically, JobAgent asks the user instead of guessing.

### 11. Verify the form

The automation verifies the fields it filled and checks the resume upload.

### 12. Review before submission

The automation stops before final submission.

The user remains responsible for reviewing and submitting the application.

---

# Testing

The project contains local tests and diagnostic scripts.

Examples include:

```text
app/application/test_browser_question_integration.py
app/application/test_question_pipeline.py
app/browser/test_browser.py
app/test_ai.py
```

Python files can be syntax checked with:

```powershell
python -m py_compile path\to\file.py
```

For example:

```powershell
python -m py_compile app\application\question_resolver.py
```

The browser-question integration test verifies the complete local question-handling path:

```text
Browser control
      ↓
Question detection
      ↓
Resolver
      ↓
Ask user when needed
      ↓
Save answer
      ↓
Fill browser control
```

---

# Current Implementation Status

## Working

- Greenhouse job collection
- Job normalization
- SQLite job storage
- Deterministic job filtering
- Seniority filtering
- Experience filtering
- Location filtering
- Local AI job matching
- Match scoring
- `APPLY` / `REVIEW` / `SKIP` recommendations
- Human job approval
- Application package generation
- Application selector
- Application question resolver
- Persistent reusable answers
- Safe profile-based answers
- Playwright browser automation
- Resume upload
- Resume upload verification
- Browser form verification
- Unknown required-question handling
- Human-controlled final submission
- Public example candidate profile
- Windows setup script
- Python dependency requirements

## In Development

- Reliable high-quality cover-letter generation
- More job-board integrations
- More robust application-question classification
- More robust browser automation
- Application tracking dashboard
- Additional automated test coverage
- React/Next.js web dashboard
- Docker setup
- CI/CD workflow
- Additional application platforms

---

# Roadmap

## Phase 1 — Job Discovery

- Greenhouse integration
- Job normalization
- SQLite storage
- Deterministic filtering

## Phase 2 — AI Matching

- Local Ollama integration
- Candidate profile
- AI job evaluation
- Match score
- Recommendation
- Safety enforcement

## Phase 3 — Application Preparation

- Human approval
- Application package generation
- Answer storage
- Question resolver
- Reliable cover-letter generation

## Phase 4 — Browser Automation

- Playwright integration
- Personal information autofill
- Resume upload
- Application question handling
- Form verification
- Safe stop before submission

## Phase 5 — Dashboard

- Web dashboard
- Job browsing
- Match-score visualization
- Application tracking
- Application status management
- Review interface

## Phase 6 — Expansion

- Additional job boards
- Better application-site support
- Improved automated tests
- Docker support
- CI/CD
- Improved documentation

---

# Design Principles

## Local First

Candidate information and AI processing should remain local whenever practical.

## Deterministic Before AI

Use reliable deterministic rules before using an AI model.

## Human Controlled

AI recommendations should not automatically become application submissions.

## Evidence Based

AI-generated application content should be based only on verified candidate information.

## No Fabrication

Never invent:

- Experience
- Qualifications
- Projects
- Achievements
- Employers
- Technologies
- Years of experience
- Application answers

## Fail Safely

When the system cannot determine a safe answer, ask the user.

## Modular

Job collection, filtering, matching, application preparation, question resolution, and browser automation are separated into individual components.

---

# Security Considerations

Never commit:

```text
.env
API keys
Authentication tokens
Browser session data
Personal resumes
Personal profile data
Application history
Saved application answers
Local databases
```

Before making a repository public, inspect:

```powershell
git status
git ls-files
```

and verify that no private files are tracked.

The public repository should contain source code and safe example configuration, not personal application data.

---

# Limitations

JobAgent is currently a personal project and is not a universal job-application automation platform.

Current limitations include:

- Job-board support is limited
- Application website structures vary significantly
- Some application questions require human input
- Some custom controls require additional handling
- Local AI performance depends on available hardware
- Cover-letter generation is still being improved
- Browser automation is currently focused on supported application flows
- Final application submission is intentionally manual
- Different job sites may require site-specific automation work
- Local AI output must still be reviewed by the user

---

# Why This Project Exists

Applying for jobs involves a large amount of repetitive work:

- Searching job boards
- Reading job descriptions
- Checking experience requirements
- Comparing skills
- Tracking suitable positions
- Filling repetitive forms
- Uploading resumes
- Answering repeated questions

JobAgent explores how much of this repetitive work can be automated locally without giving an AI unrestricted control over the application process.

The objective is not:

> **"Apply to everything automatically."**

The objective is:

> **Reduce repetitive work while keeping the candidate in control.**

---

# Disclaimer

JobAgent is a personal automation and experimentation project.

Users are responsible for:

- Reviewing generated content
- Ensuring application information is accurate
- Confirming qualifications
- Reviewing application questions
- Following the terms and policies of job websites
- Making the final decision to submit an application

The project should not be used to submit misleading, fraudulent, or inaccurate applications.

Automating interactions with a third-party website may also be subject to that website's terms and policies. Users should verify that their intended use is permitted.

---

# License

This project is licensed under the **MIT License**.

See the [`LICENSE`](LICENSE) file for the complete license text.

---

# Author

**MD SAFI MAAZ**

Frontend Web Developer

- GitHub: https://github.com/SafiMaaz01
- LinkedIn: https://www.linkedin.com/in/safimaaz01/
- Portfolio: https://safimaaz01portfolio.vercel.app/

---

## Project Status

JobAgent is an actively developed local-first automation project.

The core job collection, deterministic filtering, local AI matching, human approval, application preparation, question resolution, and Playwright autofill workflow are functional.

The project continues to evolve toward a more complete job-application assistant while maintaining its central principle:

> **Automate the repetitive parts. Keep the important decisions human.**
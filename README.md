# JobAgent — Local AI-Powered Job Application Assistant

> A local-first, privacy-respecting job application assistant that automates job discovery, deterministic relevance filtering, local AI match scoring, application package preparation, and browser form autofill — while keeping all final submission decisions under human control.

---

## 1. Executive Summary

Searching for jobs manually involves opening dozens of browser tabs, evaluating repetitive job descriptions, and filling out identical form fields over and over. **JobAgent** automates the labor-intensive stages of job discovery, matching, and form filling while maintaining strict human-in-the-loop safety.

Key highlights:
- **100% Local AI Matching**: Uses Ollama running locally (default: `qwen2.5:7b`) to evaluate job descriptions against candidate profiles without sending private resume data to paid cloud APIs.
- **Deterministic Filtering**: Fast rule-based filtering (roles, seniority, experience limits, locations) runs before AI evaluation to minimize LLM compute overhead.
- **Modern Full-Stack Control Dashboard**: A high-performance Next.js 15 App Router frontend backed by a FastAPI REST API for searching jobs, reviewing matches, managing application packages, and monitoring live browser automation tasks.
- **Human-in-the-Loop Submission Gate**: Playwright browser automation fills form fields, uploads resume PDFs, and answers custom questions, but **stops at a Ready to Submit gate requiring explicit human review and confirmation** before any form is submitted.

---

## 2. Complete End-to-End System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Next.js Web Control Dashboard                          │
│                          http://localhost:3000 (App Router)                     │
├─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────┤
│  📊 Dashboard   │  ✓ Review Queue │ 💼 Jobs Directory│ 📝 Applications │⚙Settings│
│  KPI Telemetry  │  Approve / Pass │ Filter & Detail │ Package & Runner│ Candidate│
└─────────────────┴────────┬────────┴─────────────────┴─────────────────┴─────────┘
                           │ HTTP REST (Native fetch, cache: "no-store", No SQLite)
┌──────────────────────────▼──────────────────────────────────────────────────────┐
│                            FastAPI Backend REST Layer                           │
│                            http://127.0.0.1:8000                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  - GET /api/stats (Pipeline counters & package telemetry)                       │
│  - GET /api/jobs & PUT /api/jobs/{id}/review (Job directory & human review)      │
│  - GET/POST /api/applications (Package preparation & detail inspection)          │
│  - POST /api/applications/{id}/autofill (Non-blocking background runner launch)  │
│  - GET/POST /api/tasks/{task_id} (Live automation logs & human confirmation gate)│
│  - GET/PUT /api/config/profile (Atomic validated profile writes to profile.json)│
└─────────┬──────────────────────────┬──────────────────────────┬─────────────────┘
          │ Direct Read/Write        │ Subprocess / Library     │ Local HTTP API
┌─────────▼─────────┐      ┌─────────▼─────────┐      ┌─────────▼─────────┐
│ SQLite Database   │      │ Playwright Runner │      │ Ollama AI Engine  │
│  (data/jobs.db)   │      │  Chromium Window  │      │ (qwen2.5:7b LLM)  │
└───────────────────┘      └───────────────────┘      └───────────────────┘
```

### Core Architecture Components

1. **Next.js Frontend (`frontend/`)**: Built using Next.js 15 App Router, React 19, and TypeScript. Uses Server Components by default for fast page loads and Client Components for interactive tables, drawers, live log streaming, and profile editing.
2. **FastAPI REST Server (`run_api.py`, `app/api/`)**: Provides asynchronous REST endpoints for frontend data fetching, background task execution, and atomic JSON profile persistence.
3. **SQLite Database (`data/jobs.db`)**: Central database storing job listings, external IDs, deterministic relevance flags, AI match scores, recommendations, human review statuses, and application timestamps.
4. **Greenhouse Collector (`app/jobs/greenhouse.py`)**: Queries public Greenhouse board APIs configured in `data/sources.json`, normalizes job schema, and performs upserts into SQLite.
5. **Deterministic Relevance Filter (`app/jobs/filter.py`)**: Applies regex rules to extract experience requirements, title keywords, and location constraints to weed out non-matching jobs instantly.
6. **Local Ollama Matcher (`app/job_matcher.py`)**: Evaluates filtered job descriptions against candidate profile data using local LLM inference. Outputs match scores (0-100), recommendations (`APPLY` / `PASS`), strong matches, missing requirements, and reasoning.
7. **Application Package Generator (`app/application/prepare.py`)**: Compiles candidate details, verified resume PDF paths, and resolved question answers into application packages saved in `data/applications/app_<job_id>.json`.
8. **Answer Resolution System (`app/application/answers.py`, `app/application/question_resolver.py`)**: Resolves common job questions against candidate profile fields and the saved answer bank (`data/answers.json`).
9. **Playwright Automation Engine (`app/browser/autofill_application.py`)**: Spawns non-headless Chromium to open job application forms, upload resume PDFs, fill personal details, and answer custom form questions.
10. **Human Submission Confirmation Gate**: Automation pauses before form submission and notifies the user. Submission occurs **only** when the user explicitly clicks "Confirm" or inputs affirmative confirmation.

---

## 3. Technology Stack

| Layer | Technology / Library | Purpose |
|---|---|---|
| **Frontend Framework** | Next.js 15 (App Router) | Server-side rendering, routing, client views |
| **Frontend Language** | TypeScript | Type safety & API contract alignment |
| **Styling** | Vanilla CSS (`globals.css`) | Custom dark theme, glassmorphism, responsive UI |
| **Backend API** | FastAPI + Uvicorn | Asynchronous REST backend & task execution |
| **Data Validation** | Pydantic v2 | Request/response schema validation |
| **Database** | SQLite 3 (`sqlite3.Row`) | Local job data & review state storage |
| **Local AI Engine** | Ollama (`qwen2.5:7b`) | Privacy-first job matching & analysis |
| **Browser Automation**| Playwright (Python) | Visible Chromium form interaction & autofill |
| **Job Collector** | Requests + Greenhouse API | Ingesting job postings from public company boards |

---

## 4. Directory & File Structure

```text
JobAgent/
├── app/                          # Core Python Application Package
│   ├── api/                      # FastAPI REST Layer
│   │   ├── routers/              # API Endpoint Routers
│   │   │   ├── applications.py   # Application packages & autofill runner
│   │   │   ├── config.py         # Profile & settings endpoints
│   │   │   ├── jobs.py           # Job directory & human review endpoints
│   │   │   ├── stats.py          # Dashboard KPI telemetry
│   │   │   └── tasks.py          # Automation task monitoring & confirmation
│   │   ├── schemas/              # Pydantic Request/Response Models
│   │   │   ├── application.py    # Application summary & detail schemas
│   │   │   ├── job.py            # Job summary, detail, & review schemas
│   │   │   ├── profile.py        # Candidate profile validation schemas
│   │   │   └── task.py           # Automation task status & action schemas
│   │   ├── deps.py               # Database dependency injection
│   │   └── main.py               # FastAPI app initialization & router registration
│   │
│   ├── application/              # Package Preparation & Answer Resolution
│   │   ├── answer.py             # Custom answer data structures
│   │   ├── answers.py            # Persistent answer bank manager (data/answers.json)
│   │   ├── prepare.py            # Application package compiler
│   │   ├── question_resolver.py   # Heuristic candidate question solver
│   │   ├── review.py             # Package inspection utilities
│   │   └── run.py                # Package execution pipeline
│   │
│   ├── approval/                 # Human Approval Workflow
│   │   └── review.py             # Database status updates for human decisions
│   │
│   ├── browser/                  # Playwright Automation (Protected Engine)
│   │   ├── autofill_application.py# Authoritative Playwright application filler
│   │   ├── inspect_application.py # Form structure inspector
│   │   └── test_browser.py       # Browser validation test script
│   │
│   ├── database/                 # SQLite Persistence
│   │   ├── db.py                 # Connection factory & non-destructive schema migrations
│   │   └── inspect_jobs.py       # Database inspection CLI helper
│   │
│   ├── jobs/                     # Collection & Relevance Filtering
│   │   ├── filter.py             # Deterministic regex relevance filter
│   │   ├── greenhouse.py         # Greenhouse job board API collector
│   │   ├── normalize.py          # Job posting schema normalizer
│   │   └── diagnose_filter.py    # Filter diagnostic CLI helper
│   │
│   ├── matcher/                  # AI Matcher Package
│   │   └── run_matcher.py        # Matcher runner execution script
│   │
│   ├── job_matcher.py            # Local Ollama AI client & matching prompt
│   └── profile.py                # Profile loader utility
│
├── data/                         # Local Data Directory (Ignored or Template Data)
│   ├── applications/             # Generated application packages (app_<job_id>.json)
│   ├── answers.json              # Reusable custom question answer bank
│   ├── jobs.db                   # SQLite database file
│   ├── profile.json              # Candidate profile data
│   ├── resume.pdf                # Candidate resume PDF file
│   └── sources.json              # Target Greenhouse company board tokens
│
├── frontend/                     # Next.js 15 Web Dashboard
│   ├── src/
│   │   ├── app/                  # App Router Pages
│   │   │   ├── applications/     # Applications Hub & Detail pages
│   │   │   ├── jobs/             # Jobs Directory page
│   │   │   ├── review/           # Review Queue page
│   │   │   ├── settings/         # Candidate Settings & Profile page
│   │   │   ├── globals.css       # Design tokens, variables, & utility classes
│   │   │   ├── layout.tsx        # Dashboard application shell & layout
│   │   │   └── page.tsx          # Main Overview Dashboard page
│   │   │
│   │   ├── components/           # UI Client & Server Components
│   │   │   ├── ApplicationDetailClient.tsx # Application inspection & runner panel
│   │   │   ├── ApplicationsClient.tsx      # Applications Hub client component
│   │   │   ├── Header.tsx                  # Top bar with workspace indicator
│   │   │   ├── JobDetailDrawer.tsx         # Slide-over job detail inspection drawer
│   │   │   ├── JobsFilterBar.tsx           # Search, score, & status toolbar
│   │   │   ├── JobsTableWithDrawer.tsx     # Paginated jobs directory table
│   │   │   ├── MetricCard.tsx              # KPI metric visual display
│   │   │   ├── RecentJobsTable.tsx         # Dashboard high-scoring jobs table
│   │   │   ├── ReviewQueueClient.tsx       # Human review decision cards
│   │   │   ├── SettingsClient.tsx          # Profile & preferences editor
│   │   │   ├── Sidebar.tsx                 # Dashboard sidebar navigation
│   │   │   └── StatusBadge.tsx             # Score & status color badges
│   │   │
│   │   └── lib/                  # Frontend Helper Libraries
│   │       ├── api.ts            # Type-safe fetch wrappers around FastAPI
│   │       └── types.ts          # TypeScript interfaces matching backend models
│   │
│   ├── package.json              # Frontend npm dependencies & scripts
│   └── tsconfig.json             # TypeScript compiler settings
│
├── howtouse                      # Complete Root-Level Usage & Command Manual
├── requirements.txt              # Python dependencies
├── run_api.py                    # FastAPI server startup script
├── setup.ps1                     # PowerShell automated setup script
└── README.md                     # Comprehensive project documentation
```

---

## 5. End-to-End Application Workflow

```text
  ┌─────────────────┐
  │ 1. Collect Jobs │  Greenhouse API → SQLite (jobs.db)
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ 2. Rule Filter  │  Regex checks: experience, title, location (is_relevant=1)
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ 3. AI Matching  │  Local Ollama (qwen2.5:7b) evaluates match score & reasoning
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ 4. Human Review │  Dashboard Review Queue (/review) → User approves job
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ 5. Prep Package │  Generate app_<job_id>.json (Candidate info + PDF + Answers)
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ 6. Autofill Form│  Playwright launches Chromium window & populates inputs
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ 7. Verification │  Browser inspects fields & pauses at READY TO SUBMIT gate
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ 8. Human Submit │  User inspects open browser & clicks "Confirm" in UI
  └─────────────────┘
```

---

## 6. Complete API Reference

FastAPI runs on `http://127.0.0.1:8000`. Full OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

### Statistics & Overview
- `GET /api/stats`: Returns pipeline counters (total jobs, relevant jobs, pending review, approved, applied, ready packages, average match score).

### Job Directory & Human Review
- `GET /api/jobs`: Query paginated jobs with search terms (`search`), review status (`status`), recommendation (`recommendation`), minimum match score (`min_score`), sorting, and page limits.
- `GET /api/jobs/{id}`: Returns detailed information for a single job including full job description and parsed AI match details.
- `GET /api/jobs/review-queue`: Fetches pending jobs recommended for application (`is_relevant=1`, `recommendation='APPLY'`, `review_status='pending'`).
- `PUT /api/jobs/{id}/review`: Submit a human review decision (`{"status": "approved"}` or `{"status": "rejected"}`).

### Application Packages & Automation
- `GET /api/applications`: Lists all prepared application packages (`data/applications/app_*.json`) and approved jobs ready for preparation.
- `GET /api/applications/{id}`: Returns application details for a job (resolved candidate fields, answer bank mappings, resume PDF path, verification checks).
- `POST /api/applications/{id}/prepare`: Triggers package compilation for an approved job.
- `POST /api/applications/{id}/autofill`: Launches the background Playwright browser automation runner for a prepared application.

### Automation Tasks & Human Confirmation
- `GET /api/tasks/status`: Returns current status of active background automation (running step, percentage progress, recent logs, waiting prompts).
- `POST /api/tasks/{task_id}/action`: Sends user confirmation (`{"action": "confirm"}`) to proceed with final form submission or cancellation (`{"action": "cancel"}`).

### Configuration & Candidate Profile
- `GET /api/config/profile`: Reads candidate profile data from `data/profile.json`.
- `PUT /api/config/profile`: Validates and atomically writes updated candidate profile data to `data/profile.json`.

---

## 7. Safety, Privacy, & Verification Guarantees

1. **100% Local AI Execution**: Job matching is processed locally via Ollama. No private profile details, contact numbers, or resume achievements are uploaded to third-party AI services.
2. **Explicit Human Confirmation Gate**: Playwright browser automation is configured to fill form inputs and pause before clicking final submission buttons. Form submission requires explicit human confirmation.
3. **Atomic Profile Storage**: Profile updates are written atomically using temporary files, flushing buffers, and file renaming (`tempfile` + `fsync` + `replace`) to prevent corrupted `data/profile.json` files.
4. **Isolated Frontend Architecture**: Next.js communicates strictly over HTTP REST endpoints (`http://127.0.0.1:8000`). Next.js does not import SQLite drivers or access `data/jobs.db` directly.
5. **No Fabricated Qualifications**: Question resolution logic relies on explicit facts present in `data/profile.json` or `data/answers.json`. Unknown questions trigger user prompts rather than inventing facts.

---

## 8. Quick Start Guide

For complete, step-by-step setup instructions on a fresh machine, refer to the root-level manual: [`howtouse`](file:///c:/Users/Maaz/Desktop/JobAgent/howtouse).

### Daily Execution Commands

#### Terminal 1 — Start FastAPI Backend:
```powershell
.\.venv\Scripts\Activate.ps1
python run_api.py
```

#### Terminal 2 — Start Next.js Dashboard:
```powershell
cd frontend
npm run dev
# Dashboard available at http://localhost:3000
```

#### Refreshing Pipeline Data (When Needed):
```powershell
# 1. Collect open job listings from Greenhouse boards
python -m app.jobs.greenhouse

# 2. Run local AI matcher against new postings
python -m app.job_matcher
```

#### Pre-Commit Code Validation:
```powershell
# Verify Python syntax across all modules
python -m compileall app run_api.py

# Verify Next.js frontend TypeScript types & production build
cd frontend
npm run build
```

---

## 9. License

JobAgent is released under the **MIT License**. See [`LICENSE`](file:///c:/Users/Maaz/Desktop/JobAgent/LICENSE) for details.
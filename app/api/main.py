"""
FastAPI application entrypoint for JobAgent.

This module initializes the FastAPI application instance, configures cross-origin resource
sharing (CORS) for the Next.js frontend, and registers all modular API routers:
- Stats: High-level dashboard KPI metrics and score summaries
- Jobs: Job directory, search, filtering, and approval review queue
- Applications: Application packages, package preparation, and browser autofill runner
- Tasks: Background task status polling, interaction, and cancellation
- Config: Candidate profile read/write, Greenhouse sources, and question answers
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import applications, config, jobs, stats, tasks

# Initialize FastAPI app with OpenAPI metadata
app = FastAPI(
    title="JobAgent API",
    description="Local API layer for JobAgent dashboard and automation",
    version="1.0.0",
)

# Enable CORS for Next.js frontend (default port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount functional API sub-routers
app.include_router(stats.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(tasks.router)
app.include_router(config.router)


@app.get("/")
def root():
    """
    Root health check endpoint.
    Used by clients to verify that the backend server is reachable and active.
    """
    return {"status": "ok", "app": "JobAgent API", "version": "1.0.0"}

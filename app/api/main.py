"""FastAPI application entrypoint for JobAgent."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import applications, config, jobs, stats, tasks

app = FastAPI(
    title="JobAgent API",
    description="Local API layer for JobAgent dashboard and automation",
    version="1.0.0",
)

# Enable CORS for Next.js development server
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

# Register routers
app.include_router(stats.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(tasks.router)
app.include_router(config.router)


@app.get("/")
def root():
    """Root health check."""
    return {"status": "ok", "app": "JobAgent API", "version": "1.0.0"}

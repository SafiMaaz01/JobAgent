"""
CLI runner script to start the JobAgent FastAPI backend.

This entry point starts the Uvicorn ASGI server hosting the JobAgent REST API.
- Host: 127.0.0.1 (Localhost only for privacy and local-first architecture)
- Port: 8000
- Reload: Enabled for fast local development and automatic reload on code changes
"""
import uvicorn

if __name__ == "__main__":
    print("Starting JobAgent API on http://127.0.0.1:8000 ...")
    # Launch Uvicorn server pointing to FastAPI app factory in app.api.main
    uvicorn.run("app.api.main:app", host="127.0.0.1", port=8000, reload=True)

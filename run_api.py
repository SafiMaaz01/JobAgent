"""CLI runner script to start the JobAgent FastAPI backend."""
import uvicorn

if __name__ == "__main__":
    print("Starting JobAgent API on http://127.0.0.1:8000 ...")
    uvicorn.run("app.api.main:app", host="127.0.0.1", port=8000, reload=True)

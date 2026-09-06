"""Automation runner orchestrator for JobAgent browser autofill."""
import os
import sys
import json
import time
import logging
import threading
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import HTTPException
from app.api.routers.tasks import update_task_state, get_task_state

logger = logging.getLogger("jobagent.automation")

BASE_DIR = Path(__file__).resolve().parents[2]


class AutomationManager:
    """Manages browser automation lifecycle, ensuring only one active run at a time."""

    def __init__(self):
        self._lock = threading.Lock()
        self._process: Optional[subprocess.Popen] = None
        self._active_job_id: Optional[int] = None
        self._active_job_info: Dict[str, Any] = {}
        self._monitor_thread: Optional[threading.Thread] = None
        self._logs: List[str] = []
        self._verification_passed: Optional[bool] = None

    def is_running(self) -> bool:
        """Check if an automation process is actively running."""
        with self._lock:
            if self._process is None:
                return False
            return self._process.poll() is None

    def get_active_job_id(self) -> Optional[int]:
        """Return the job ID currently running automation, if any."""
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                return self._active_job_id
            return None

    def start_autofill(self, job_id: int, package_path: Path, job_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start the authoritative browser autofill process for a prepared application.
        Guarantees single concurrency and non-blocking execution.
        """
        with self._lock:
            # 1. Concurrency check
            if self._process is not None and self._process.poll() is None:
                if self._active_job_id == job_id:
                    # Return existing task state without launching a duplicate process
                    current_state = get_task_state()
                    return {
                        "task": "autofill",
                        "status": current_state.get("status", "running"),
                        "message": current_state.get("message", "Automation already running for this job"),
                        "progress": current_state.get("progress", 0),
                        "job_id": job_id,
                        "already_running": True,
                    }
                else:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Another automation process is currently running for Job #{self._active_job_id}.",
                    )

            # 2. Reset state for new run
            self._active_job_id = job_id
            self._active_job_info = job_info
            self._logs = []
            self._verification_passed = None

            initial_details = {
                "job_id": job_id,
                "company": job_info.get("company", "Unknown"),
                "role": job_info.get("title", "Unknown"),
                "stage": "initializing",
                "verification_passed": None,
                "recent_logs": ["Initializing browser automation..."],
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

            update_task_state(
                task="autofill",
                status="running",
                message=f"Starting autofill for {job_info.get('company')} - {job_info.get('title')}",
                progress=10,
                details=initial_details,
            )

            # 3. Launch subprocess calling the authoritative autofill_application.main(package_path)
            # UTF-8 encoding and unbuffered binary python output ensures reliable pipe decoding on Windows
            py_code = (
                "import sys; "
                "from app.browser.autofill_application import main; "
                "main(sys.argv[1])"
            )

            cmd = [
                sys.executable,
                "-u",
                "-c",
                py_code,
                str(package_path.resolve()),
            ]

            try:
                self._process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    cwd=str(BASE_DIR),
                )
            except Exception as e:
                self._active_job_id = None
                self._process = None
                update_task_state(
                    task="autofill",
                    status="error",
                    message=f"Failed to start automation process: {str(e)}",
                    progress=0,
                    details={"job_id": job_id, "error": str(e)},
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to launch browser automation process: {str(e)}",
                )

            # 4. Spawn background thread to monitor process output without blocking FastAPI
            self._monitor_thread = threading.Thread(
                target=self._monitor_process,
                args=(self._process, job_id, job_info),
                daemon=True,
            )
            self._monitor_thread.start()

            return {
                "task": "autofill",
                "status": "running",
                "message": f"Browser automation launched for {job_info.get('company')} - {job_info.get('title')}",
                "progress": 10,
                "job_id": job_id,
                "already_running": False,
            }

    def _monitor_process(self, process: subprocess.Popen, job_id: int, job_info: Dict[str, Any]):
        """Background thread monitoring the stdout of the autofill subprocess."""
        logger.info("Started monitoring automation process for Job #%s", job_id)
        current_stage = "initializing"
        progress = 10
        status = "running"
        message = f"Starting autofill for {job_info.get('company')}"

        try:
            for raw_line in iter(process.stdout.readline, ""):
                line = raw_line.strip()
                if not line:
                    continue

                self._logs.append(line)
                if len(self._logs) > 50:
                    self._logs = self._logs[-50:]

                # Detect lifecycle milestones
                line_lower = line.lower()

                if "opening application page" in line_lower or "navigating" in line_lower:
                    current_stage = "navigating"
                    progress = 25
                    message = "Opening application form in Chromium..."
                elif "uploading resume" in line_lower or "resume upload" in line_lower:
                    current_stage = "uploading_resume"
                    progress = 40
                    message = "Uploading candidate resume..."
                elif "handling candidate" in line_lower or "filling standard" in line_lower:
                    current_stage = "filling_profile"
                    progress = 55
                    message = "Filling candidate personal & contact details..."
                elif "handling education" in line_lower or "handling verified" in line_lower or "handling custom" in line_lower:
                    current_stage = "answering_questions"
                    progress = 70
                    message = "Answering application questions & selecting custom fields..."
                elif "internship availability required" in line_lower:
                    current_stage = "internship_required"
                    status = "waiting_for_input"
                    message = "Internship availability choice required (1-4)."
                elif "verifying application state" in line_lower or "browser-state verification" in line_lower:
                    current_stage = "verifying"
                    progress = 85
                    message = "Verifying form field states in browser..."
                elif "browser-state verification passed" in line_lower:
                    self._verification_passed = True
                elif "safe stop" in line_lower:
                    current_stage = "safe_stop"
                    status = "error"
                    progress = 90
                    message = "Autofill stopped safely: verification failed or unknown required questions remain."
                elif "ready to submit" in line_lower:
                    current_stage = "ready_to_submit"
                    status = "waiting_for_confirmation"
                    progress = 95
                    message = "Autofill verified! Paused at human confirmation gate. Not submitted."
                elif "submission cancelled" in line_lower:
                    current_stage = "cancelled"
                    status = "cancelled"
                    message = "Submission cancelled by human. Browser closed safely. No application submitted."
                elif "application submitted" in line_lower:
                    current_stage = "submitted"
                    status = "completed"
                    progress = 100
                    message = "Application submitted successfully!"
                    self._mark_application_applied(job_id)

                details = {
                    "job_id": job_id,
                    "company": job_info.get("company", "Unknown"),
                    "role": job_info.get("title", "Unknown"),
                    "stage": current_stage,
                    "verification_passed": self._verification_passed,
                    "recent_logs": self._logs[-15:],
                    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }

                update_task_state(
                    task="autofill",
                    status=status,
                    message=message,
                    progress=progress,
                    details=details,
                )

        except Exception as err:
            logger.error("Error reading automation stdout: %s", err)
        finally:
            process.wait()
            logger.info("Automation process exited with code %s", process.returncode)

            # Finalize task state if not already set to completed/cancelled/error
            final_status = get_task_state().get("status", "running")
            if final_status in ("running", "waiting_for_confirmation", "waiting_for_input"):
                if process.returncode == 0 and self._verification_passed:
                    final_status = "completed"
                    final_msg = "Automation session ended cleanly."
                elif process.returncode == 0:
                    final_status = "cancelled"
                    final_msg = "Browser automation session closed."
                else:
                    final_status = "error"
                    final_msg = f"Browser automation process ended with code {process.returncode}."

                update_task_state(
                    task="autofill",
                    status=final_status,
                    message=final_msg,
                    progress=100 if final_status == "completed" else progress,
                    details={
                        "job_id": job_id,
                        "company": job_info.get("company", "Unknown"),
                        "role": job_info.get("title", "Unknown"),
                        "stage": current_stage,
                        "verification_passed": self._verification_passed,
                        "recent_logs": self._logs[-15:],
                        "exit_code": process.returncode,
                    },
                )

            with self._lock:
                if self._active_job_id == job_id:
                    self._active_job_id = None
                    self._process = None

    def respond(self, action: str, value: Optional[str] = None) -> Dict[str, Any]:
        """Send input to the running automation process (e.g. human confirmation or cancellation)."""
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                raise HTTPException(
                    status_code=400,
                    detail="No active browser automation process is currently running.",
                )

            action_lower = action.lower()
            try:
                if action_lower in ("cancel", "no", "n", "abort"):
                    # Send "n\n\n" to reject submission and dismiss "Press Enter to close"
                    if self._process.stdin:
                        self._process.stdin.write("n\n\n")
                        self._process.stdin.flush()
                    update_task_state(
                        task="autofill",
                        status="cancelled",
                        message="Human rejected submission. Closing browser safely...",
                        progress=95,
                        details={
                            "job_id": self._active_job_id,
                            "stage": "cancelling",
                            "recent_logs": self._logs[-10:],
                        },
                    )
                    return {"success": True, "message": "Submission cancelled; closing browser."}

                elif action_lower in ("confirm", "yes", "y", "submit"):
                    # Note: Only manual human action can invoke this; frontend never auto-submits.
                    if self._process.stdin:
                        self._process.stdin.write("y\n\n")
                        self._process.stdin.flush()
                    update_task_state(
                        task="autofill",
                        status="running",
                        message="Human confirmed submission. Submitting in browser...",
                        progress=98,
                        details={
                            "job_id": self._active_job_id,
                            "stage": "submitting",
                            "recent_logs": self._logs[-10:],
                        },
                    )
                    return {"success": True, "message": "Submission confirmed; submitting in browser."}

                elif action_lower == "input" and value is not None:
                    # Provide text input (e.g. for internship cohort selection 1-4)
                    if self._process.stdin:
                        self._process.stdin.write(f"{value}\n")
                        self._process.stdin.flush()
                    return {"success": True, "message": f"Input '{value}' sent to automation."}

                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unrecognized automation action: {action}",
                    )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to communicate with automation process: {str(e)}",
                )

    def cancel(self) -> Dict[str, Any]:
        """Safely terminate the automation process if running."""
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                return {"success": True, "message": "No active automation process."}

            job_id = self._active_job_id
            try:
                if self._process.stdin:
                    self._process.stdin.write("n\n\n")
                    self._process.stdin.flush()
                # Wait briefly for clean exit
                time.sleep(1.0)
                if self._process.poll() is None:
                    self._process.terminate()
            except Exception:
                try:
                    self._process.terminate()
                except Exception:
                    pass

            update_task_state(
                task="autofill",
                status="cancelled",
                message="Automation process was stopped by user.",
                progress=0,
                details={"job_id": job_id, "stage": "stopped"},
            )
            self._active_job_id = None
            self._process = None
            return {"success": True, "message": "Automation process stopped."}

    def _mark_application_applied(self, job_id: int):
        """Authoritatively mark application as applied only after real submission is verified."""
        try:
            from app.database.db import get_connection

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE jobs SET status = 'applied', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (job_id,),
            )
            conn.commit()
            conn.close()

            package_file = BASE_DIR / "data" / "applications" / f"job_{job_id}.json"
            if package_file.exists():
                with package_file.open("r", encoding="utf-8") as f:
                    pkg = json.load(f)
                pkg.setdefault("application", {})["status"] = "applied"
                pkg["application"]["submitted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                with package_file.open("w", encoding="utf-8") as f:
                    json.dump(pkg, f, indent=2)
            logger.info("Application package and database updated to 'applied' for Job #%s", job_id)
        except Exception as e:
            logger.error("Failed to mark application as applied: %s", e)


# Global singleton instance
automation_manager = AutomationManager()

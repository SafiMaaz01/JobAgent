"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ApplicationSummary, JobSummary, TaskStatus } from "@/lib/types";
import {
  prepareApplicationPackage,
  getApplications,
  getEligibleJobsForPreparation,
  startAutofill,
  getTaskStatus,
  cancelTask,
} from "@/lib/api";
import { MatchScoreBadge, RecommendationBadge, ReviewStatusBadge } from "./StatusBadge";

interface ApplicationsClientProps {
  initialApplications: ApplicationSummary[];
  initialEligibleJobs: JobSummary[];
}

export default function ApplicationsClient({
  initialApplications,
  initialEligibleJobs,
}: ApplicationsClientProps) {
  const [applications, setApplications] = useState<ApplicationSummary[]>(initialApplications);
  const [eligibleJobs, setEligibleJobs] = useState<JobSummary[]>(initialEligibleJobs);
  const [preparingId, setPreparingId] = useState<number | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const activeJobId = taskStatus?.details?.job_id;
  const isTaskRunning =
    taskStatus?.task === "autofill" &&
    (taskStatus.status === "running" ||
      taskStatus.status === "waiting_for_confirmation" ||
      taskStatus.status === "waiting_for_input");

  const checkGlobalTask = async () => {
    try {
      const status = await getTaskStatus();
      setTaskStatus(status);
      if (status.status === "completed") {
        // Refresh application list if completed
        const updatedApps = await getApplications();
        setApplications(updatedApps);
      }
    } catch {
      // Ignore polling errors
    }
  };

  useEffect(() => {
    checkGlobalTask();
  }, []);

  useEffect(() => {
    if (isTaskRunning) {
      pollingRef.current = setInterval(checkGlobalTask, 1500);
    } else if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [isTaskRunning]);

  const handlePreparePackage = async (jobId: number) => {
    setPreparingId(jobId);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const result = await prepareApplicationPackage(jobId);
      setSuccessMessage(result.message);

      // Refresh both lists
      const [updatedApps, updatedEligible] = await Promise.all([
        getApplications(),
        getEligibleJobsForPreparation(),
      ]);
      setApplications(updatedApps);
      setEligibleJobs(updatedEligible);
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : `Failed to prepare application package for job #${jobId}`
      );
    } finally {
      setPreparingId(null);
    }
  };

  const handleStartAutofill = async (jobId: number) => {
    setErrorMessage(null);
    try {
      const res = await startAutofill(jobId);
      setTaskStatus(res);
      setSuccessMessage(res.message);
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : `Failed to launch autofill for job #${jobId}`
      );
    }
  };

  const handleCancelTask = async () => {
    try {
      await cancelTask();
      await checkGlobalTask();
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : "Failed to cancel automation"
      );
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      {/* Notifications */}
      {successMessage && (
        <div
          style={{
            background: "var(--success-surface)",
            border: "1px solid rgba(16, 185, 129, 0.4)",
            color: "#6ee7b7",
            padding: "12px 16px",
            borderRadius: "var(--radius-lg)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>✓ {successMessage}</span>
          <button
            onClick={() => setSuccessMessage(null)}
            style={{
              background: "transparent",
              border: "none",
              color: "#6ee7b7",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            ✕
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="error-banner">
          <div className="error-title">Action Error</div>
          <div>{errorMessage}</div>
        </div>
      )}

      {/* Global Active Automation Banner */}
      {isTaskRunning && taskStatus && (
        <div
          style={{
            background: "var(--bg-surface)",
            border:
              taskStatus.status === "waiting_for_confirmation"
                ? "1px solid rgba(245, 158, 11, 0.7)"
                : "1px solid var(--brand)",
            borderRadius: "var(--radius-lg)",
            padding: "18px 22px",
            boxShadow:
              taskStatus.status === "waiting_for_confirmation"
                ? "0 4px 20px rgba(245, 158, 11, 0.2)"
                : "0 4px 20px rgba(59, 130, 246, 0.15)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span
                style={{
                  display: "inline-block",
                  width: "10px",
                  height: "10px",
                  borderRadius: "50%",
                  backgroundColor:
                    taskStatus.status === "waiting_for_confirmation"
                      ? "var(--warning)"
                      : "var(--brand)",
                  animation: "pulse 1.5s infinite",
                }}
              />
              <span style={{ fontWeight: "700", fontSize: "14px", color: "var(--text-primary)" }}>
                Active Autofill Runner: {taskStatus.details?.company} — {taskStatus.details?.role}
              </span>
            </div>

            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              {activeJobId && (
                <Link
                  href={`/applications/${activeJobId}`}
                  style={{
                    background: "var(--brand-surface)",
                    border: "1px solid var(--brand)",
                    color: "var(--brand-light)",
                    borderRadius: "var(--radius-sm)",
                    padding: "4px 10px",
                    fontSize: "12px",
                    fontWeight: "600",
                    textDecoration: "none",
                  }}
                >
                  View Details & Logs →
                </Link>
              )}
              <button
                onClick={handleCancelTask}
                style={{
                  background: "var(--danger-surface)",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  color: "var(--danger)",
                  borderRadius: "var(--radius-sm)",
                  padding: "4px 10px",
                  fontSize: "12px",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                Cancel / Close Browser
              </button>
            </div>
          </div>

          {/* Progress bar */}
          <div
            style={{
              width: "100%",
              height: "5px",
              backgroundColor: "var(--border-color)",
              borderRadius: "3px",
              overflow: "hidden",
              marginBottom: "8px",
            }}
          >
            <div
              style={{
                width: `${taskStatus.progress}%`,
                height: "100%",
                backgroundColor:
                  taskStatus.status === "waiting_for_confirmation"
                    ? "var(--warning)"
                    : "var(--brand)",
                transition: "width 0.4s ease",
              }}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "var(--text-secondary)" }}>
            <span>{taskStatus.message}</span>
            <span style={{ fontFamily: "monospace" }}>{taskStatus.progress}%</span>
          </div>
        </div>
      )}

      {/* Section 1: Prepared Application Packages */}
      <div>
        <div className="section-header">
          <div>
            <h2 className="section-title">Application Packages</h2>
            <p className="page-subtitle">
              Generated packages ready for review and authoritative browser autofill
            </p>
          </div>
          <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
            {applications.length} package{applications.length === 1 ? "" : "s"} found
          </span>
        </div>

        {applications.length === 0 ? (
          <div className="table-container">
            <div className="empty-state">
              <div className="empty-state-title">No application packages found</div>
              <div className="empty-state-desc">
                Approved jobs must have their application package prepared before submission.
              </div>
            </div>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: "80px" }}>Score</th>
                  <th>Company</th>
                  <th>Job Title</th>
                  <th>Location</th>
                  <th style={{ width: "130px" }}>Package Status</th>
                  <th style={{ width: "100px" }}>Resume</th>
                  <th style={{ width: "100px" }}>Created</th>
                  <th style={{ width: "240px", textAlign: "right" }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((app) => {
                  const isAppRunning = isTaskRunning && activeJobId === app.job_id;
                  const isApplied = app.application_status === "applied";
                  const isApproved = app.review_status === "approved";
                  const canAutofill = isApproved && !isApplied && !isTaskRunning;

                  return (
                    <tr key={app.job_id}>
                      <td>
                        <MatchScoreBadge score={app.match_score} />
                      </td>
                      <td style={{ fontWeight: "600", color: "var(--text-primary)" }}>
                        {app.company}
                      </td>
                      <td>
                        <div style={{ fontWeight: "500" }}>{app.title}</div>
                        <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                          ID #{app.job_id}
                        </div>
                      </td>
                      <td style={{ color: "var(--text-secondary)" }}>
                        {app.location || "Remote / Not specified"}
                      </td>
                      <td>
                        <span
                          className="badge"
                          style={{
                            backgroundColor:
                              isApplied
                                ? "var(--purple-surface)"
                                : app.application_status === "ready_for_review"
                                ? "var(--success-surface)"
                                : "var(--bg-subtle)",
                            color:
                              isApplied
                                ? "var(--purple)"
                                : app.application_status === "ready_for_review"
                                ? "var(--success)"
                                : "var(--text-secondary)",
                            border:
                              isApplied
                                ? "1px solid rgba(139, 92, 246, 0.3)"
                                : "1px solid rgba(16, 185, 129, 0.3)",
                          }}
                        >
                          {isApplied
                            ? "Submitted / Applied"
                            : app.application_status === "ready_for_review"
                            ? "Ready for Review"
                            : app.application_status}
                        </span>
                      </td>
                      <td>
                        {app.has_resume ? (
                          <span style={{ fontSize: "12px", color: "var(--success)" }}>
                            ✓ PDF
                          </span>
                        ) : (
                          <span style={{ fontSize: "12px", color: "var(--danger)" }}>
                            ✕ Missing
                          </span>
                        )}
                      </td>
                      <td style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                        {app.created_at ? app.created_at.split("T")[0] : "—"}
                      </td>

                      <td style={{ textAlign: "right" }}>
                        <div style={{ display: "inline-flex", gap: "8px", alignItems: "center" }}>
                          {isAppRunning ? (
                            <span
                              style={{
                                fontSize: "12px",
                                color: "var(--brand-light)",
                                fontWeight: "600",
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "4px",
                              }}
                            >
                              ⚙️ Autofilling...
                            </span>
                          ) : canAutofill ? (
                            <button
                              onClick={() => handleStartAutofill(app.job_id)}
                              style={{
                                background: "var(--brand)",
                                border: "none",
                                color: "#fff",
                                borderRadius: "var(--radius-sm)",
                                padding: "5px 10px",
                                fontSize: "12px",
                                fontWeight: "600",
                                cursor: "pointer",
                              }}
                            >
                              ▶ Run Autofill
                            </button>
                          ) : isApplied ? (
                            <span style={{ fontSize: "12px", color: "var(--purple)", fontWeight: "500" }}>
                              ✓ Applied
                            </span>
                          ) : null}

                          <Link
                            href={`/applications/${app.job_id}`}
                            style={{
                              background: "var(--brand-surface)",
                              border: "1px solid var(--brand)",
                              color: "var(--brand-light)",
                              borderRadius: "var(--radius-sm)",
                              padding: "5px 10px",
                              fontSize: "12px",
                              fontWeight: "600",
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                              textDecoration: "none",
                            }}
                          >
                            Inspect →
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Section 2: Approved Jobs Eligible for Package Preparation */}
      <div>
        <div className="section-header">
          <div>
            <h2 className="section-title">Approved Jobs Awaiting Package Preparation</h2>
            <p className="page-subtitle">
              Jobs approved during review that need an application package prepared
            </p>
          </div>
          <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
            {eligibleJobs.length} eligible
          </span>
        </div>

        {eligibleJobs.length === 0 ? (
          <div className="table-container">
            <div className="empty-state">
              <div className="empty-state-title">No approved jobs awaiting preparation</div>
              <div className="empty-state-desc">
                All approved jobs have application packages prepared. Review more jobs in the{" "}
                <Link href="/review" style={{ color: "var(--brand-light)" }}>
                  Review Queue
                </Link>
                .
              </div>
            </div>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: "80px" }}>Score</th>
                  <th>Company</th>
                  <th>Job Title</th>
                  <th>Location</th>
                  <th style={{ width: "130px" }}>Review Status</th>
                  <th style={{ width: "120px" }}>Recommendation</th>
                  <th style={{ width: "170px", textAlign: "right" }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {eligibleJobs.map((job) => (
                  <tr key={job.id}>
                    <td>
                      <MatchScoreBadge score={job.match_score} />
                    </td>
                    <td style={{ fontWeight: "600", color: "var(--text-primary)" }}>
                      {job.company}
                    </td>
                    <td>
                      <div style={{ fontWeight: "500" }}>{job.title}</div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                        ID #{job.id}
                      </div>
                    </td>
                    <td style={{ color: "var(--text-secondary)" }}>
                      {job.location || "Remote / Not specified"}
                    </td>
                    <td>
                      <ReviewStatusBadge status={job.review_status} />
                    </td>
                    <td>
                      <RecommendationBadge recommendation={job.recommendation} />
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <button
                        onClick={() => handlePreparePackage(job.id)}
                        disabled={preparingId === job.id}
                        style={{
                          background: "var(--brand)",
                          border: "none",
                          color: "#ffffff",
                          borderRadius: "var(--radius-sm)",
                          padding: "6px 14px",
                          fontSize: "12px",
                          fontWeight: "600",
                          cursor: preparingId === job.id ? "not-allowed" : "pointer",
                          opacity: preparingId === job.id ? 0.7 : 1,
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "6px",
                        }}
                      >
                        {preparingId === job.id ? "Preparing..." : "Prepare Package"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

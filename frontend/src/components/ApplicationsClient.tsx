"use client";

import React, { useState, useEffect, useRef } from "react";
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
import ScoreRing from "@/components/ui/ScoreRing";
import { ReviewStatusBadge } from "./StatusBadge";
import { useToast } from "@/components/ui/Toast";
import {
  FileCheck,
  Play,
  Square,
  ArrowRight,
  Building2,
  MapPin,
  Sparkles,
  Loader2,
  CheckCircle2,
  FileText,
  AlertTriangle,
} from "lucide-react";

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
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const { showToast } = useToast();

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
    try {
      const result = await prepareApplicationPackage(jobId);
      showToast("Package Prepared", result.message, "success");

      const [updatedApps, updatedEligible] = await Promise.all([
        getApplications(),
        getEligibleJobsForPreparation(),
      ]);
      setApplications(updatedApps);
      setEligibleJobs(updatedEligible);
    } catch (err: unknown) {
      showToast(
        "Preparation Failed",
        err instanceof Error ? err.message : "Failed to prepare package",
        "error"
      );
    } finally {
      setPreparingId(null);
    }
  };

  const handleStartAutofill = async (jobId: number) => {
    try {
      const res = await startAutofill(jobId);
      setTaskStatus(res);
      showToast("Automation Started", res.message, "info");
    } catch (err: unknown) {
      showToast(
        "Autofill Failed",
        err instanceof Error ? err.message : "Failed to launch autofill runner",
        "error"
      );
    }
  };

  const handleCancelTask = async () => {
    try {
      await cancelTask();
      await checkGlobalTask();
      showToast("Task Cancelled", "Playwright runner stopped", "info");
    } catch (err: unknown) {
      showToast(
        "Cancel Failed",
        err instanceof Error ? err.message : "Failed to cancel automation",
        "error"
      );
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      {/* Active Automation Banner */}
      {isTaskRunning && taskStatus && (
        <div
          className="glass-card"
          style={{
            padding: "20px 24px",
            borderColor:
              taskStatus.status === "waiting_for_confirmation"
                ? "var(--warning-border)"
                : "var(--border-glow)",
            background:
              taskStatus.status === "waiting_for_confirmation"
                ? "var(--warning-surface)"
                : "var(--accent-surface)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <Loader2 size={20} className="animate-spin" color="var(--accent-light)" />
              <div>
                <div style={{ fontWeight: "800", fontSize: "15px", color: "var(--text-primary)" }}>
                  Active Browser Automation Runner: {taskStatus.details?.company} — {taskStatus.details?.role}
                </div>
                <div style={{ fontSize: "12.5px", color: "var(--text-secondary)", marginTop: "2px" }}>
                  {taskStatus.message}
                </div>
              </div>
            </div>

            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              {activeJobId && (
                <Link href={`/applications/${activeJobId}`} className="btn-primary" style={{ padding: "6px 12px", fontSize: "12px" }}>
                  <span>Inspect Control Room</span>
                  <ArrowRight size={14} />
                </Link>
              )}
              <button onClick={handleCancelTask} className="btn-danger" style={{ padding: "6px 12px", fontSize: "12px" }}>
                <Square size={14} />
                <span>Stop Runner</span>
              </button>
            </div>
          </div>

          <div style={{ width: "100%", height: "6px", background: "var(--bg-surface-0)", borderRadius: "3px", overflow: "hidden" }}>
            <div style={{ width: `${taskStatus.progress}%`, height: "100%", background: "var(--accent-primary)", transition: "width 0.4s ease" }} />
          </div>
        </div>
      )}

      {/* Prepared Application Packages Table */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h2 className="section-title">Application Packages Hub</h2>
            <p className="caption-text">
              Generated candidate packages (JSON metadata, resume PDF, cover letter, QA answers)
            </p>
          </div>
          <span className="mono-text" style={{ fontSize: "12px", color: "var(--text-muted)" }}>
            {applications.length} Packages
          </span>
        </div>

        {applications.length === 0 ? (
          <div className="glass-card" style={{ padding: "48px 24px", textAlign: "center", color: "var(--text-muted)" }}>
            <FileText size={28} style={{ margin: "0 auto 12px auto" }} />
            <div style={{ fontSize: "15px", fontWeight: "600", color: "var(--text-primary)" }}>
              No application packages prepared yet
            </div>
            <div style={{ fontSize: "13px", marginTop: "4px" }}>
              Approved jobs will appear below in the Preparation Queue.
            </div>
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: "70px", textAlign: "center" }}>Match</th>
                  <th>Company & Role</th>
                  <th>Location</th>
                  <th style={{ width: "140px" }}>Status</th>
                  <th style={{ width: "100px" }}>Resume</th>
                  <th style={{ width: "110px" }}>Created</th>
                  <th style={{ width: "220px", textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((app) => {
                  const isAppRunning = isTaskRunning && activeJobId === app.job_id;
                  const isApplied = app.application_status === "applied" || app.application_status === "submitted";
                  const isApproved = app.review_status === "approved";
                  const canAutofill = isApproved && !isApplied && !isTaskRunning;

                  return (
                    <tr key={app.job_id}>
                      <td style={{ textAlign: "center" }}>
                        <ScoreRing score={app.match_score} size={38} strokeWidth={3.5} />
                      </td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                          <div
                            style={{
                              width: "34px",
                              height: "34px",
                              borderRadius: "var(--radius-sm)",
                              background: "var(--bg-surface-1)",
                              border: "1px solid var(--border-subtle)",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              color: "var(--accent-light)",
                              fontWeight: "700",
                              fontSize: "13px",
                              flexShrink: 0,
                            }}
                          >
                            <Building2 size={16} />
                          </div>
                          <div>
                            <div style={{ fontWeight: "700", color: "var(--text-primary)", fontSize: "13.5px" }}>
                              {app.title}
                            </div>
                            <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "1px" }}>
                              {app.company}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-secondary)", fontSize: "12.5px" }}>
                          <MapPin size={13} color="var(--text-muted)" />
                          <span>{app.location || "Remote / Flexible"}</span>
                        </div>
                      </td>
                      <td>
                        <span
                          className="badge-semantic"
                          style={{
                            background: isApplied ? "var(--success-surface)" : "var(--accent-surface)",
                            color: isApplied ? "var(--success)" : "var(--accent-light)",
                            border: isApplied ? "1px solid var(--success-border)" : "1px solid var(--border-glow)",
                          }}
                        >
                          {isApplied ? "Submitted" : app.application_status}
                        </span>
                      </td>
                      <td>
                        {app.has_resume ? (
                          <span style={{ fontSize: "12px", color: "var(--success)", fontWeight: "600" }}>
                            ✓ PDF Ready
                          </span>
                        ) : (
                          <span style={{ fontSize: "12px", color: "var(--danger)", fontWeight: "600" }}>
                            ✕ Missing
                          </span>
                        )}
                      </td>
                      <td className="mono-text" style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                        {app.created_at ? app.created_at.split("T")[0] : "—"}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <div style={{ display: "inline-flex", gap: "8px", alignItems: "center" }}>
                          {isAppRunning ? (
                            <span style={{ fontSize: "12px", color: "var(--accent-light)", fontWeight: "600", display: "inline-flex", alignItems: "center", gap: "6px" }}>
                              <Loader2 size={13} className="animate-spin" />
                              <span>Autofilling...</span>
                            </span>
                          ) : canAutofill ? (
                            <button
                              onClick={() => handleStartAutofill(app.job_id)}
                              className="btn-primary"
                              style={{ padding: "5px 10px", fontSize: "11.5px" }}
                            >
                              <Play size={12} />
                              <span>Run Autofill</span>
                            </button>
                          ) : isApplied ? (
                            <span style={{ fontSize: "12px", color: "var(--success)", fontWeight: "600" }}>
                              ✓ Submitted
                            </span>
                          ) : null}

                          <Link
                            href={`/applications/${app.job_id}`}
                            className="btn-secondary"
                            style={{ padding: "5px 10px", fontSize: "11.5px" }}
                          >
                            <span>Inspect Control Room</span>
                            <ArrowRight size={12} />
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

      {/* Approved Jobs Awaiting Package Preparation */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h2 className="section-title">Approved Jobs Awaiting Package Preparation</h2>
            <p className="caption-text">
              Approved opportunities from Review Queue needing package generation
            </p>
          </div>
          <span className="mono-text" style={{ fontSize: "12px", color: "var(--text-muted)" }}>
            {eligibleJobs.length} Eligible
          </span>
        </div>

        {eligibleJobs.length === 0 ? (
          <div className="glass-card" style={{ padding: "48px 24px", textAlign: "center", color: "var(--text-muted)" }}>
            <CheckCircle2 size={28} style={{ margin: "0 auto 12px auto" }} />
            <div style={{ fontSize: "15px", fontWeight: "600", color: "var(--text-primary)" }}>
              No approved jobs awaiting package preparation
            </div>
            <div style={{ fontSize: "13px", marginTop: "4px" }}>
              All approved listings have been processed. Review more opportunities in the{" "}
              <Link href="/review" style={{ color: "var(--accent-light)", fontWeight: "600" }}>
                Review Queue
              </Link>
              .
            </div>
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: "70px", textAlign: "center" }}>Score</th>
                  <th>Company & Role</th>
                  <th>Location</th>
                  <th style={{ width: "120px" }}>Review Status</th>
                  <th style={{ width: "170px", textAlign: "right" }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {eligibleJobs.map((job) => (
                  <tr key={job.id}>
                    <td style={{ textAlign: "center" }}>
                      <ScoreRing score={job.match_score} size={38} strokeWidth={3.5} />
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                        <div
                          style={{
                            width: "34px",
                            height: "34px",
                            borderRadius: "var(--radius-sm)",
                            background: "var(--bg-surface-1)",
                            border: "1px solid var(--border-subtle)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: "var(--accent-light)",
                            fontWeight: "700",
                            fontSize: "13px",
                            flexShrink: 0,
                          }}
                        >
                          <Building2 size={16} />
                        </div>
                        <div>
                          <div style={{ fontWeight: "700", color: "var(--text-primary)", fontSize: "13.5px" }}>
                            {job.title}
                          </div>
                          <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "1px" }}>
                            {job.company}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-secondary)", fontSize: "12.5px" }}>
                        <MapPin size={13} color="var(--text-muted)" />
                        <span>{job.location || "Remote / Flexible"}</span>
                      </div>
                    </td>
                    <td>
                      <ReviewStatusBadge status={job.review_status} />
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <button
                        onClick={() => handlePreparePackage(job.id)}
                        disabled={preparingId === job.id}
                        className="btn-primary"
                        style={{ padding: "6px 14px", fontSize: "12px" }}
                      >
                        {preparingId === job.id ? <Loader2 size={14} className="animate-spin" /> : <FileCheck size={14} />}
                        <span>{preparingId === job.id ? "Generating Package..." : "Prepare Package"}</span>
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

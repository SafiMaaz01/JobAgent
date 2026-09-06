"use client";

/**
 * Interactive client component for inspecting application packages and controlling browser automation.
 * 
 * Features:
 * - Candidate profile & resolved answer bank preview
 * - Automation runner panel with Start Autofill trigger
 * - Real-time task polling and terminal log stream
 * - Interactive Ready to Submit gate with human confirmation (Confirm / Cancel)
 */
import { useState, useEffect, useRef } from "react";
import Link from "next/link";

import { ApplicationDetail, TaskStatus } from "@/lib/types";
import { startAutofill, getTaskStatus, cancelTask, respondToTask, getApplicationDetail } from "@/lib/api";
import { MatchScoreBadge, RecommendationBadge, ReviewStatusBadge } from "./StatusBadge";

interface ApplicationDetailClientProps {
  initialApp: ApplicationDetail;
}

export default function ApplicationDetailClient({ initialApp }: ApplicationDetailClientProps) {
  const [app, setApp] = useState<ApplicationDetail>(initialApp);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [showLogs, setShowLogs] = useState(true);
  const [internshipInput, setInternshipInput] = useState("1");
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const candidate = app.candidate || {};
  const personal = (candidate.personal as Record<string, string>) || {};
  const links = (candidate.links as Record<string, string>) || {};
  const education = (candidate.education as Record<string, string>) || {};
  const experience = (candidate.experience as Record<string, unknown>) || {};
  const preferences = (candidate.preferences as Record<string, string>) || {};
  const skills = Array.isArray(candidate.skills) ? (candidate.skills as string[]) : [];
  const match = app.match_details;

  const isApplied = app.application_status === "applied";
  const isApproved = app.review_status === "approved";
  const canRunAutofill = isApproved && !isApplied && !isRunning;

  // Poll task status while active
  const checkTaskStatus = async () => {
    try {
      const status = await getTaskStatus();
      if (status.task === "autofill" && status.details?.job_id === app.job_id) {
        setTaskStatus(status);
        const active =
          status.status === "running" ||
          status.status === "waiting_for_confirmation" ||
          status.status === "waiting_for_input";
        setIsRunning(active);

        // If completed, refresh application data
        if (status.status === "completed") {
          const freshApp = await getApplicationDetail(app.job_id);
          setApp(freshApp);
        }
      } else if (status.task === "autofill" && isRunning) {
        // Task was for another job or ended
        setTaskStatus(status);
        setIsRunning(false);
      }
    } catch {
      // Ignore transient polling errors
    }
  };

  useEffect(() => {
    // Initial check on mount
    checkTaskStatus();
  }, []);

  useEffect(() => {
    if (isRunning) {
      pollingRef.current = setInterval(checkTaskStatus, 1500);
    } else if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [isRunning]);

  const handleStartAutofill = async () => {
    setActionError(null);
    try {
      const res = await startAutofill(app.job_id);
      setTaskStatus(res);
      setIsRunning(true);
    } catch (err: unknown) {
      setActionError(
        err instanceof Error ? err.message : "Failed to launch browser automation"
      );
    }
  };

  const handleCancelAutomation = async () => {
    setActionError(null);
    try {
      await cancelTask();
      await checkTaskStatus();
    } catch (err: unknown) {
      setActionError(
        err instanceof Error ? err.message : "Failed to cancel automation"
      );
    }
  };

  const handleSendInput = async () => {
    setActionError(null);
    try {
      await respondToTask("input", internshipInput);
      await checkTaskStatus();
    } catch (err: unknown) {
      setActionError(
        err instanceof Error ? err.message : "Failed to send input"
      );
    }
  };

  const currentDetails = taskStatus?.details;
  const isWaitingForConfirmation = taskStatus?.status === "waiting_for_confirmation";
  const isWaitingForInput = taskStatus?.status === "waiting_for_input";
  const isTaskActiveForThisJob = taskStatus?.details?.job_id === app.job_id && taskStatus?.task === "autofill";

  return (
    <div style={{ maxWidth: "1100px" }}>
      {/* Back Link */}
      <div style={{ marginBottom: "16px" }}>
        <Link
          href="/applications"
          style={{
            fontSize: "13px",
            color: "var(--brand-light)",
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            fontWeight: "500",
          }}
        >
          ← Back to Applications Hub
        </Link>
      </div>

      {/* Header Banner */}
      <div
        style={{
          background: "var(--bg-surface)",
          border: "1px solid var(--border-color)",
          borderRadius: "var(--radius-lg)",
          padding: "24px",
          marginBottom: "24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
              Job ID #{app.job_id}
            </span>
            {app.review_status && <ReviewStatusBadge status={app.review_status} />}
            <span
              className="badge"
              style={{
                backgroundColor: isApplied ? "var(--purple-surface)" : "var(--success-surface)",
                color: isApplied ? "var(--purple)" : "var(--success)",
                border: isApplied ? "1px solid rgba(139, 92, 246, 0.3)" : "1px solid rgba(16, 185, 129, 0.3)",
              }}
            >
              {isApplied ? "Submitted / Applied" : "Package Ready for Review"}
            </span>
          </div>

          <h1 style={{ fontSize: "22px", fontWeight: "700", color: "var(--text-primary)" }}>
            {app.role}
          </h1>
          <div style={{ fontSize: "14px", color: "var(--text-secondary)", marginTop: "4px" }}>
            <strong style={{ color: "var(--text-primary)" }}>{app.company}</strong> •{" "}
            {app.location || "Remote / Not specified"}
          </div>

          {app.created_at && (
            <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "8px" }}>
              Package generated: {app.created_at.split("T")[0]}
            </div>
          )}
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "10px" }}>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            {app.job_url && (
              <a
                href={app.job_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  background: "transparent",
                  border: "1px solid var(--border-color)",
                  color: "var(--text-primary)",
                  borderRadius: "var(--radius-sm)",
                  padding: "8px 14px",
                  fontSize: "13px",
                  fontWeight: "500",
                  textDecoration: "none",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                Open Job Board ↗
              </a>
            )}

            {canRunAutofill && (
              <button
                onClick={handleStartAutofill}
                style={{
                  background: "var(--brand)",
                  border: "none",
                  color: "#ffffff",
                  borderRadius: "var(--radius-sm)",
                  padding: "8px 18px",
                  fontSize: "13px",
                  fontWeight: "600",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  boxShadow: "0 2px 8px rgba(59, 130, 246, 0.3)",
                }}
              >
                ▶ Run Autofill
              </button>
            )}

            {isApplied && (
              <span
                style={{
                  background: "var(--purple-surface)",
                  color: "var(--purple)",
                  padding: "8px 14px",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "13px",
                  fontWeight: "600",
                  border: "1px solid rgba(139, 92, 246, 0.4)",
                }}
              >
                ✓ Application Applied
              </span>
            )}
          </div>

          {!isApproved && (
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              Job must be approved before running automation
            </span>
          )}
        </div>
      </div>

      {/* Action Error Banner */}
      {actionError && (
        <div className="error-banner" style={{ marginBottom: "20px" }}>
          <div className="error-title">Automation Error</div>
          <div>{actionError}</div>
        </div>
      )}

      {/* Live Automation Runner Card */}
      {isTaskActiveForThisJob && taskStatus && (
        <div
          style={{
            background: "var(--bg-surface)",
            border: isWaitingForConfirmation
              ? "1px solid rgba(245, 158, 11, 0.6)"
              : "1px solid var(--brand)",
            borderRadius: "var(--radius-lg)",
            padding: "20px",
            marginBottom: "24px",
            boxShadow: isWaitingForConfirmation
              ? "0 4px 20px rgba(245, 158, 11, 0.15)"
              : "0 4px 20px rgba(59, 130, 246, 0.1)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span
                style={{
                  display: "inline-block",
                  width: "10px",
                  height: "10px",
                  borderRadius: "50%",
                  backgroundColor:
                    taskStatus.status === "completed"
                      ? "var(--success)"
                      : isWaitingForConfirmation
                      ? "var(--warning)"
                      : "var(--brand)",
                  animation: isRunning ? "pulse 1.5s infinite" : "none",
                }}
              />
              <span style={{ fontWeight: "700", fontSize: "15px", color: "var(--text-primary)" }}>
                Browser Automation:{" "}
                {isWaitingForConfirmation
                  ? "Ready to Submit (Human Gate)"
                  : isWaitingForInput
                  ? "Input Required"
                  : taskStatus.status === "completed"
                  ? "Completed"
                  : taskStatus.status === "cancelled"
                  ? "Cancelled"
                  : "Running"}
              </span>
            </div>

            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              <span style={{ fontSize: "12px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                Stage: {currentDetails?.stage || "active"} ({taskStatus.progress}%)
              </span>
              {(isRunning || isWaitingForConfirmation) && (
                <button
                  onClick={handleCancelAutomation}
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
                  Cancel & Close Browser
                </button>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          <div
            style={{
              width: "100%",
              height: "6px",
              backgroundColor: "var(--border-color)",
              borderRadius: "3px",
              overflow: "hidden",
              marginBottom: "12px",
            }}
          >
            <div
              style={{
                width: `${taskStatus.progress}%`,
                height: "100%",
                backgroundColor: isWaitingForConfirmation ? "var(--warning)" : "var(--brand)",
                transition: "width 0.4s ease",
              }}
            />
          </div>

          {/* Status Message */}
          <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginBottom: "12px" }}>
            {taskStatus.message}
          </div>

          {/* Human Confirmation Gate Banner */}
          {isWaitingForConfirmation && (
            <div
              style={{
                background: "rgba(245, 158, 11, 0.1)",
                border: "1px solid rgba(245, 158, 11, 0.4)",
                borderRadius: "var(--radius-md)",
                padding: "16px",
                marginBottom: "16px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                <span style={{ fontSize: "18px" }}>⚠️</span>
                <span style={{ fontWeight: "700", color: "#fcd34d", fontSize: "14px" }}>
                  Authoritative Human Submission Confirmation Gate
                </span>
              </div>
              <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: "0 0 12px 0", lineHeight: "1.5" }}>
                The application form was autofilled and verified in the Chromium browser window.
                The automation is paused at the <strong>READY TO SUBMIT</strong> gate.
                The application has <strong>NOT</strong> been sent to the employer.
              </p>
              <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
                <button
                  onClick={handleCancelAutomation}
                  style={{
                    background: "var(--danger-surface)",
                    border: "1px solid rgba(239, 68, 68, 0.4)",
                    color: "var(--danger)",
                    borderRadius: "var(--radius-sm)",
                    padding: "6px 14px",
                    fontSize: "12px",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  Cancel Submission & Close Browser
                </button>
                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Review the open browser window. Final confirmation can be completed in console or canceled above.
                </span>
              </div>
            </div>
          )}

          {/* Internship Availability Input Banner */}
          {isWaitingForInput && (
            <div
              style={{
                background: "rgba(59, 130, 246, 0.1)",
                border: "1px solid rgba(59, 130, 246, 0.4)",
                borderRadius: "var(--radius-md)",
                padding: "14px",
                marginBottom: "16px",
              }}
            >
              <div style={{ fontWeight: "600", color: "var(--brand-light)", marginBottom: "8px", fontSize: "13px" }}>
                Interactive Input Required: Internship Availability Cohort
              </div>
              <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                <select
                  value={internshipInput}
                  onChange={(e) => setInternshipInput(e.target.value)}
                  style={{
                    background: "var(--bg-input)",
                    border: "1px solid var(--border-color)",
                    color: "var(--text-primary)",
                    borderRadius: "var(--radius-sm)",
                    padding: "6px 10px",
                    fontSize: "12px",
                  }}
                >
                  <option value="1">1. Summer (May - August)</option>
                  <option value="2">2. Fall (September - December)</option>
                  <option value="3">3. Winter/Spring (January - April)</option>
                  <option value="4">4. Full-Year Co-op</option>
                </select>
                <button
                  onClick={handleSendInput}
                  style={{
                    background: "var(--brand)",
                    border: "none",
                    color: "#fff",
                    borderRadius: "var(--radius-sm)",
                    padding: "6px 14px",
                    fontSize: "12px",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  Submit Selection
                </button>
              </div>
            </div>
          )}

          {/* Verification Status Badge */}
          {currentDetails?.verification_passed && (
            <div
              style={{
                background: "var(--success-surface)",
                border: "1px solid rgba(16, 185, 129, 0.3)",
                borderRadius: "var(--radius-md)",
                padding: "10px 14px",
                marginBottom: "12px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                fontSize: "12px",
                color: "var(--success)",
              }}
            >
              <span>✓</span>
              <span>
                <strong>Browser-State Verification Passed:</strong> All deterministic profile fields and required questions verified.
              </span>
            </div>
          )}

          {/* Terminal Logs Collapsible */}
          <div>
            <button
              onClick={() => setShowLogs(!showLogs)}
              style={{
                background: "transparent",
                border: "none",
                color: "var(--text-muted)",
                fontSize: "11px",
                fontWeight: "600",
                cursor: "pointer",
                padding: "4px 0",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              {showLogs ? "▼ Hide Execution Logs" : "▶ Show Live Execution Logs"}
            </button>

            {showLogs && currentDetails?.recent_logs && (
              <div
                style={{
                  marginTop: "8px",
                  background: "#0d1117",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "var(--radius-sm)",
                  padding: "10px 12px",
                  fontFamily: "monospace",
                  fontSize: "11px",
                  color: "#c9d1d9",
                  maxHeight: "180px",
                  overflowY: "auto",
                  lineHeight: "1.4",
                }}
              >
                {currentDetails.recent_logs.map((logLine, idx) => (
                  <div key={idx} style={{ whiteSpace: "pre-wrap" }}>
                    {logLine}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "24px" }}>
        {/* Left Column: Application Details */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Section: Candidate Profile */}
          <div
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-color)",
              borderRadius: "var(--radius-lg)",
              padding: "20px",
            }}
          >
            <h2 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px", color: "var(--text-primary)" }}>
              Candidate Profile for this Application
            </h2>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div>
                <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Full Name
                </span>
                <div style={{ fontSize: "14px", fontWeight: "500", color: "var(--text-primary)" }}>
                  {personal.full_name || "—"}
                </div>
              </div>

              <div>
                <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Email Address
                </span>
                <div style={{ fontSize: "14px", fontWeight: "500", color: "var(--text-primary)" }}>
                  {personal.email || "—"}
                </div>
              </div>

              <div>
                <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Phone Number
                </span>
                <div style={{ fontSize: "14px", fontWeight: "500", color: "var(--text-primary)" }}>
                  {personal.phone || "—"}
                </div>
              </div>

              <div>
                <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Location
                </span>
                <div style={{ fontSize: "14px", fontWeight: "500", color: "var(--text-primary)" }}>
                  {personal.location || "—"}
                </div>
              </div>

              {education.institution && (
                <div>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                    Education
                  </span>
                  <div style={{ fontSize: "13px", color: "var(--text-primary)" }}>
                    {education.institution} ({education.degree || "Degree"})
                  </div>
                </div>
              )}

              {preferences.legal_authorization && (
                <div>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                    Work Authorization
                  </span>
                  <div style={{ fontSize: "13px", color: "var(--text-primary)" }}>
                    {preferences.legal_authorization}
                  </div>
                </div>
              )}
            </div>

            {/* Candidate Online Profiles */}
            <div style={{ marginTop: "16px", paddingTop: "12px", borderTop: "1px solid var(--border-color)" }}>
              <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                Candidate Web Profiles
              </span>
              <div style={{ display: "flex", gap: "16px", marginTop: "6px", flexWrap: "wrap" }}>
                {links.linkedin && (
                  <a
                    href={links.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontSize: "12px", color: "var(--brand-light)" }}
                  >
                    LinkedIn ↗
                  </a>
                )}
                {links.github && (
                  <a
                    href={links.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontSize: "12px", color: "var(--brand-light)" }}
                  >
                    GitHub ↗
                  </a>
                )}
                {links.portfolio && (
                  <a
                    href={links.portfolio}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontSize: "12px", color: "var(--brand-light)" }}
                  >
                    Portfolio ↗
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Section: Saved Questionnaire Answers */}
          <div
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-color)",
              borderRadius: "var(--radius-lg)",
              padding: "20px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "16px", fontWeight: "600", color: "var(--text-primary)" }}>
                Saved Questionnaire Responses
              </h2>
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                {Object.keys(app.resolved_answers || {}).length} questions mapped
              </span>
            </div>

            {Object.keys(app.resolved_answers || {}).length === 0 ? (
              <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                No custom application questions recorded in package.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {Object.entries(app.resolved_answers).map(([questionKey, answerValue], idx) => (
                  <div
                    key={idx}
                    style={{
                      background: "var(--bg-subtle)",
                      borderRadius: "var(--radius-md)",
                      padding: "12px 16px",
                      border: "1px solid var(--border-color)",
                    }}
                  >
                    <div style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-secondary)", marginBottom: "4px" }}>
                      {questionKey.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                    </div>
                    <div style={{ fontSize: "13px", color: "var(--text-primary)", fontWeight: "500" }}>
                      {typeof answerValue === "object" ? JSON.stringify(answerValue) : String(answerValue)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Package Metadata & Match Assessment */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Resume Verification Card */}
          <div
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-color)",
              borderRadius: "var(--radius-lg)",
              padding: "20px",
            }}
          >
            <h3 style={{ fontSize: "14px", fontWeight: "600", color: "var(--text-primary)", marginBottom: "12px" }}>
              Attached Resume Document
            </h3>

            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
              <span style={{ fontSize: "20px" }}>📄</span>
              <div>
                <div style={{ fontSize: "13px", fontWeight: "600", color: "var(--text-primary)" }}>
                  {app.resume_path || "data/resume.pdf"}
                </div>
                <div style={{ fontSize: "11px", color: app.resume_exists ? "var(--success)" : "var(--danger)" }}>
                  {app.resume_exists ? "✓ File verified on filesystem" : "✕ File not found"}
                </div>
              </div>
            </div>
          </div>

          {/* Match Assessment */}
          <div
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-color)",
              borderRadius: "var(--radius-lg)",
              padding: "20px",
            }}
          >
            <h3 style={{ fontSize: "14px", fontWeight: "600", color: "var(--text-primary)", marginBottom: "12px" }}>
              AI Match Assessment
            </h3>

            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
              <MatchScoreBadge score={app.match_score} />
              <RecommendationBadge recommendation={app.recommendation} />
            </div>

            {match && (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {match.reason && (
                  <div>
                    <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                      Reasoning
                    </span>
                    <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px", lineHeight: "1.5" }}>
                      {match.reason}
                    </p>
                  </div>
                )}

                {match.strong_matches && match.strong_matches.length > 0 && (
                  <div>
                    <span style={{ fontSize: "11px", color: "var(--success)", textTransform: "uppercase", fontWeight: "600" }}>
                      Strengths ({match.strong_matches.length})
                    </span>
                    <ul style={{ margin: "4px 0 0 16px", padding: 0, fontSize: "12px", color: "var(--text-secondary)" }}>
                      {match.strong_matches.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {match.minimum_requirements_missing && match.minimum_requirements_missing.length > 0 && (
                  <div>
                    <span style={{ fontSize: "11px", color: "var(--danger)", textTransform: "uppercase", fontWeight: "600" }}>
                      Missing Requirements
                    </span>
                    <ul style={{ margin: "4px 0 0 16px", padding: 0, fontSize: "12px", color: "var(--text-secondary)" }}>
                      {match.minimum_requirements_missing.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

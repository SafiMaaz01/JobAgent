"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ApplicationDetail, TaskStatus } from "@/lib/types";
import { startAutofill, getTaskStatus, cancelTask, respondToTask, getApplicationDetail, markApplicationSubmitted } from "@/lib/api";
import ScoreRing from "@/components/ui/ScoreRing";
import { ReviewStatusBadge } from "./StatusBadge";
import { useToast } from "@/components/ui/Toast";
import {
  ArrowLeft,
  Building2,
  MapPin,
  ExternalLink,
  Play,
  Square,
  CheckCircle2,
  AlertTriangle,
  FileText,
  ShieldAlert,
  Sparkles,
  Loader2,
  User,
  Check,
  XCircle,
} from "lucide-react";

interface ApplicationDetailClientProps {
  initialApp: ApplicationDetail;
}

export default function ApplicationDetailClient({ initialApp }: ApplicationDetailClientProps) {
  const [app, setApp] = useState<ApplicationDetail>(initialApp);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [showLogs, setShowLogs] = useState(true);
  const [internshipInput, setInternshipInput] = useState("1");
  const [activeTab, setActiveTab] = useState<"overview" | "answers" | "candidate" | "resume">("overview");
  const [showMarkSubmittedModal, setShowMarkSubmittedModal] = useState(false);
  const [isSubmittingManual, setIsSubmittingManual] = useState(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const { showToast } = useToast();

  const candidate = app.candidate || {};
  const personal = (candidate.personal as Record<string, string>) || {};
  const links = (candidate.links as Record<string, string>) || {};
  const education = (candidate.education as Record<string, string>) || {};
  const preferences = (candidate.preferences as Record<string, string>) || {};
  const match = app.match_details;

  const isApplied = app.review_status === "applied";
  const isApproved = app.review_status === "approved";
  const canRunAutofill = isApproved && !isApplied && !isRunning;

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

        if (status.status === "completed") {
          const freshApp = await getApplicationDetail(app.job_id);
          setApp(freshApp);
          showToast("Autofill Completed", "Application package processed", "success");
        }
      } else if (status.task === "autofill" && isRunning) {
        setTaskStatus(status);
        setIsRunning(false);
      }
    } catch {
      // Ignore polling errors
    }
  };

  useEffect(() => {
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
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [isRunning]);

  const handleStartAutofill = async () => {
    try {
      const res = await startAutofill(app.job_id);
      setTaskStatus(res);
      setIsRunning(true);
      showToast("Autofill Runner Started", res.message, "info");
    } catch (err: unknown) {
      showToast(
        "Automation Error",
        err instanceof Error ? err.message : "Failed to launch runner",
        "error"
      );
    }
  };

  const handleCancelAutomation = async () => {
    try {
      await cancelTask();
      await checkTaskStatus();
      showToast("Task Cancelled", "Runner stopped", "info");
    } catch (err: unknown) {
      showToast(
        "Cancel Error",
        err instanceof Error ? err.message : "Failed to cancel automation",
        "error"
      );
    }
  };

  const handleSendInput = async () => {
    try {
      await respondToTask("input", internshipInput);
      await checkTaskStatus();
      showToast("Input Sent", "Selection submitted to runner", "success");
    } catch (err: unknown) {
      showToast(
        "Input Error",
        err instanceof Error ? err.message : "Failed to send input",
        "error"
      );
    }
  };

  const handleConfirmMarkSubmitted = async () => {
    setIsSubmittingManual(true);
    try {
      const res = await markApplicationSubmitted(app.job_id);
      setIsRunning(false);
      setShowMarkSubmittedModal(false);

      const freshApp = await getApplicationDetail(app.job_id);
      setApp(freshApp);
      await checkTaskStatus();

      showToast(
        "Application Marked as Submitted",
        res.message,
        "success"
      );
    } catch (err: unknown) {
      showToast(
        "Action Failed",
        err instanceof Error ? err.message : "Failed to mark application as submitted",
        "error"
      );
    } finally {
      setIsSubmittingManual(false);
    }
  };

  const currentDetails = taskStatus?.details;
  const isWaitingForConfirmation = taskStatus?.status === "waiting_for_confirmation";
  const isWaitingForInput = taskStatus?.status === "waiting_for_input";
  const isTaskActiveForThisJob = taskStatus?.details?.job_id === app.job_id && taskStatus?.task === "autofill";

  return (
    <div style={{ maxWidth: "1160px", margin: "0 auto" }}>
      {/* Navigation Link */}
      <div style={{ marginBottom: "18px" }}>
        <Link href="/applications" className="btn-secondary" style={{ padding: "6px 12px", fontSize: "12px" }}>
          <ArrowLeft size={14} />
          <span>Back to Applications Control Hub</span>
        </Link>
      </div>

      {/* Hero Control Room Header */}
      <div
        className="glass-card"
        style={{
          padding: "24px 28px",
          marginBottom: "28px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "16px",
          background: "linear-gradient(135deg, rgba(19, 27, 46, 0.95) 0%, rgba(26, 36, 61, 0.95) 100%)",
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-start", gap: "16px" }}>
          <ScoreRing score={app.match_score} size={54} strokeWidth={4.5} />
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
              <span className="mono-text" style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                JOB #{app.job_id}
              </span>
              {app.review_status && <ReviewStatusBadge status={app.review_status} />}
              <span
                className="badge-semantic"
                style={{
                  background: isApplied ? "var(--success-surface)" : "var(--accent-surface)",
                  color: isApplied ? "var(--success)" : "var(--accent-light)",
                  border: isApplied ? "1px solid var(--success-border)" : "1px solid var(--border-glow)",
                }}
              >
                {isApplied ? "Submitted Application" : "Package Ready for Review"}
              </span>
            </div>

            <h1 style={{ fontSize: "22px", fontWeight: "800", color: "var(--text-primary)" }}>
              {app.role}
            </h1>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "4px", fontSize: "13.5px", color: "var(--text-secondary)" }}>
              <span style={{ fontWeight: "700", color: "var(--text-primary)" }}>{app.company}</span>
              <span>•</span>
              <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <MapPin size={13} color="var(--text-muted)" />
                <span>{app.location || "Remote / Flexible"}</span>
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "10px" }}>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            {app.job_url && (
              <a
                href={app.job_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary"
                style={{ padding: "8px 14px", fontSize: "12.5px" }}
              >
                <span>External Listing</span>
                <ExternalLink size={13} />
              </a>
            )}

            {!isApplied && (
              <button
                onClick={() => setShowMarkSubmittedModal(true)}
                className="btn-secondary"
                style={{ padding: "8px 14px", fontSize: "12.5px" }}
              >
                <CheckCircle2 size={14} color="var(--success)" />
                <span>Mark as Submitted</span>
              </button>
            )}

            {canRunAutofill && (
              <button onClick={handleStartAutofill} className="btn-primary">
                <Play size={15} />
                <span>Run Playwright Autofill</span>
              </button>
            )}

            {isApplied && (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "4px" }}>
                <span className="badge-semantic badge-submitted" style={{ padding: "6px 12px", fontSize: "12px" }}>
                  <CheckCircle2 size={14} />
                  <span>Application Submitted</span>
                </span>
                {app.applied_at && (
                  <span className="mono-text" style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    {app.submission_source === "manual" ? "Submitted manually" : "Submitted"} • {app.applied_at.replace("T", " ").split(".")[0]}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Authoritative Human Confirmation Gate Banner (Directive #14) */}
      {!isApplied && isWaitingForConfirmation && isTaskActiveForThisJob && (
        <div
          className="glass-card"
          style={{
            padding: "24px",
            marginBottom: "28px",
            borderColor: "var(--warning-border)",
            background: "linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(19, 27, 46, 0.95) 100%)",
            boxShadow: "0 0 30px rgba(245, 158, 11, 0.2)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "var(--radius-md)",
                background: "var(--warning-surface)",
                border: "1px solid var(--warning-border)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--warning)",
              }}
            >
              <ShieldAlert size={22} />
            </div>
            <div>
              <div style={{ fontWeight: "800", fontSize: "16px", color: "var(--warning)" }}>
                MANDATORY HUMAN SUBMISSION CONFIRMATION GATE
              </div>
              <div style={{ fontSize: "12.5px", color: "var(--text-secondary)", marginTop: "2px" }}>
                Form autofill & verification checks completed. Review required before sending application.
              </div>
            </div>
          </div>

          <p style={{ fontSize: "13.5px", color: "var(--text-primary)", lineHeight: "1.6", marginBottom: "16px" }}>
            The Chromium browser has populated all required form fields, attached your resume PDF, and verified questionnaire inputs. The system is currently holding at the <strong>READY TO SUBMIT</strong> safety gate. No submission has occurred.
          </p>

          <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
            <button onClick={handleCancelAutomation} className="btn-danger">
              <Square size={15} />
              <span>Cancel & Close Browser</span>
            </button>

            <button
              onClick={() => setShowMarkSubmittedModal(true)}
              className="btn-secondary"
              style={{
                padding: "6px 14px",
                fontSize: "12px",
                background: "var(--success-surface)",
                borderColor: "var(--success-border)",
                color: "var(--success)",
              }}
            >
              <CheckCircle2 size={14} />
              <span>Mark as Submitted Externally</span>
            </button>

            <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              To complete final submission, inspect the open Chromium browser window and confirm human submission.
            </span>
          </div>
        </div>
      )}

      {/* Control Room Navigation Tabs */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          marginBottom: "24px",
          borderBottom: "1px solid var(--border-subtle)",
          paddingBottom: "12px",
        }}
      >
        {[
          { id: "overview", label: "Overview & Runner", icon: Play },
          { id: "answers", label: "Resolved QA Answers", icon: FileText },
          { id: "candidate", label: "Candidate Profile", icon: User },
          { id: "resume", label: "Resume & Verification", icon: CheckCircle2 },
        ].map((tab) => {
          const IconComp = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={isActive ? "btn-primary" : "btn-secondary"}
              style={{ padding: "8px 16px", fontSize: "12.5px" }}
            >
              <IconComp size={14} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Overview & Runner */}
      {activeTab === "overview" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "24px" }}>
          {/* Automation Runner State Card */}
          <div className="glass-card" style={{ padding: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Sparkles size={18} color="var(--accent-light)" />
                <h3 className="section-title">Playwright Browser Automation Controls</h3>
              </div>
              <span className="mono-text" style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                Status: {taskStatus ? taskStatus.status.toUpperCase() : "IDLE"}
              </span>
            </div>

            {isTaskActiveForThisJob && taskStatus ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div style={{ fontSize: "13px", color: "var(--text-primary)" }}>
                  {taskStatus.message}
                </div>
                <div style={{ width: "100%", height: "8px", background: "var(--bg-surface-0)", borderRadius: "4px", overflow: "hidden" }}>
                  <div style={{ width: `${taskStatus.progress}%`, height: "100%", background: "var(--accent-primary)", transition: "width 0.4s ease" }} />
                </div>

                {isWaitingForInput && (
                  <div style={{ background: "var(--accent-surface)", border: "1px solid var(--border-glow)", padding: "14px", borderRadius: "var(--radius-md)", display: "flex", gap: "12px", alignItems: "center" }}>
                    <select
                      className="select-field"
                      value={internshipInput}
                      onChange={(e) => setInternshipInput(e.target.value)}
                    >
                      <option value="1">1. Summer (May - August)</option>
                      <option value="2">2. Fall (September - December)</option>
                      <option value="3">3. Winter/Spring (January - April)</option>
                      <option value="4">4. Full-Year Co-op</option>
                    </select>
                    <button onClick={handleSendInput} className="btn-primary" style={{ padding: "8px 14px", fontSize: "12px" }}>
                      Submit Cohort Input
                    </button>
                  </div>
                )}

                {/* Execution Logs */}
                <div>
                  <button onClick={() => setShowLogs(!showLogs)} style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: "12px", cursor: "pointer" }}>
                    {showLogs ? "▼ Hide Execution Terminal Logs" : "▶ Show Execution Terminal Logs"}
                  </button>
                  {showLogs && currentDetails?.recent_logs && (
                    <div className="mono-text" style={{ marginTop: "10px", background: "#0d1117", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "12px", fontSize: "11px", color: "#c9d1d9", maxHeight: "200px", overflowY: "auto" }}>
                      {currentDetails.recent_logs.map((log, idx) => (
                        <div key={idx}>{log}</div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                No active automation runner process currently attached to this job package. Click <strong>Run Playwright Autofill</strong> above to execute local browser automation.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Resolved QA Answers */}
      {activeTab === "answers" && (
        <div className="glass-card" style={{ padding: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <div>
              <h3 className="section-title">Resolved Application QA Answers</h3>
              <p className="caption-text">Exact question & candidate answer key-value pairs used for form completion</p>
            </div>
            <span className="mono-text" style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              {Object.keys(app.resolved_answers || {}).length} Mapped Pairs
            </span>
          </div>

          {Object.keys(app.resolved_answers || {}).length === 0 ? (
            <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "40px" }}>
              No custom questionnaire answers stored in this package.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {Object.entries(app.resolved_answers).map(([key, val], idx) => (
                <div key={idx} style={{ background: "var(--bg-surface-0)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "14px 18px" }}>
                  <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--accent-light)", marginBottom: "4px" }}>
                    {key.replace(/_/g, " ").toUpperCase()}
                  </div>
                  <div style={{ fontSize: "13.5px", color: "var(--text-primary)", fontWeight: "500" }}>
                    {typeof val === "object" ? JSON.stringify(val) : String(val)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Candidate Profile */}
      {activeTab === "candidate" && (
        <div className="glass-card" style={{ padding: "24px" }}>
          <h3 className="section-title" style={{ marginBottom: "18px" }}>Candidate Profile Snapshot</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", fontSize: "13px" }}>
            <div>
              <div style={{ color: "var(--text-muted)", fontSize: "11px", textTransform: "uppercase" }}>Full Name</div>
              <div style={{ color: "var(--text-primary)", fontWeight: "700", marginTop: "2px" }}>{personal.full_name || "—"}</div>
            </div>
            <div>
              <div style={{ color: "var(--text-muted)", fontSize: "11px", textTransform: "uppercase" }}>Email Address</div>
              <div style={{ color: "var(--text-primary)", fontWeight: "700", marginTop: "2px" }}>{personal.email || "—"}</div>
            </div>
            <div>
              <div style={{ color: "var(--text-muted)", fontSize: "11px", textTransform: "uppercase" }}>Phone</div>
              <div style={{ color: "var(--text-primary)", marginTop: "2px" }}>{personal.phone || "—"}</div>
            </div>
            <div>
              <div style={{ color: "var(--text-muted)", fontSize: "11px", textTransform: "uppercase" }}>Location</div>
              <div style={{ color: "var(--text-primary)", marginTop: "2px" }}>{personal.location || "—"}</div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Resume & Verification */}
      {activeTab === "resume" && (
        <div className="glass-card" style={{ padding: "24px" }}>
          <h3 className="section-title" style={{ marginBottom: "16px" }}>Resume PDF & Package Verification</h3>
          <div style={{ display: "flex", alignItems: "center", gap: "14px", padding: "16px", background: "var(--bg-surface-0)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)" }}>
            <FileText size={28} color="var(--accent-light)" />
            <div>
              <div className="mono-text" style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-primary)" }}>
                {app.resume_path || "data/resume.pdf"}
              </div>
              <div style={{ fontSize: "12px", color: app.resume_exists ? "var(--success)" : "var(--danger)", marginTop: "2px" }}>
                {app.resume_exists ? "✓ Local PDF file verified" : "✕ File missing on disk"}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Dialog for External Submission Confirmation */}
      {showMarkSubmittedModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(10, 15, 29, 0.8)",
            backdropFilter: "blur(6px)",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "16px",
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget && !isSubmittingManual) {
              setShowMarkSubmittedModal(false);
            }
          }}
        >
          <div
            className="glass-card"
            style={{
              width: "100%",
              maxWidth: "480px",
              padding: "28px",
              borderRadius: "var(--radius-lg)",
              background: "linear-gradient(135deg, rgba(19, 27, 46, 0.98) 0%, rgba(26, 36, 61, 0.98) 100%)",
              boxShadow: "0 20px 40px rgba(0, 0, 0, 0.6), 0 0 1px 1px var(--border-glow)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
              <div
                style={{
                  width: "40px",
                  height: "40px",
                  borderRadius: "var(--radius-md)",
                  background: "var(--success-surface)",
                  border: "1px solid var(--success-border)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--success)",
                  flexShrink: 0,
                }}
              >
                <CheckCircle2 size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: "17px", fontWeight: "800", color: "var(--text-primary)" }}>
                  Confirm external submission
                </h3>
                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Job #{app.job_id} • {app.company}
                </span>
              </div>
            </div>

            <p
              style={{
                fontSize: "13.5px",
                color: "var(--text-secondary)",
                lineHeight: "1.6",
                marginBottom: "20px",
                background: "var(--bg-surface-0)",
                padding: "14px",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              Only use this if you have already submitted this application on the external job site. JobAgent will not submit anything.
            </p>

            {isTaskActiveForThisJob && (
              <div style={{ fontSize: "12px", color: "var(--warning)", marginBottom: "20px", display: "flex", alignItems: "center", gap: "6px" }}>
                <AlertTriangle size={14} />
                <span>Active browser automation runner will be cancelled safely.</span>
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
              <button
                onClick={() => setShowMarkSubmittedModal(false)}
                disabled={isSubmittingManual}
                className="btn-secondary"
                style={{ padding: "8px 16px", fontSize: "13px" }}
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmMarkSubmitted}
                disabled={isSubmittingManual}
                className="btn-primary"
                style={{
                  padding: "8px 18px",
                  fontSize: "13px",
                  background: "var(--success)",
                  borderColor: "var(--success-border)",
                }}
              >
                {isSubmittingManual ? (
                  <>
                    <Loader2 size={15} className="animate-spin" />
                    <span>Marking Submitted...</span>
                  </>
                ) : (
                  <span>Yes, Mark Submitted</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

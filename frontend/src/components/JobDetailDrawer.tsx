"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { JobDetail } from "@/lib/types";
import { getJobDetail, submitReview } from "@/lib/api";
import ScoreRing from "@/components/ui/ScoreRing";
import { RecommendationBadge, ReviewStatusBadge } from "./StatusBadge";
import { useToast } from "@/components/ui/Toast";
import {
  X,
  Building2,
  MapPin,
  ExternalLink,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Check,
  FileText,
} from "lucide-react";

interface JobDetailDrawerProps {
  jobId: number | null;
  onClose: () => void;
}

export default function JobDetailDrawer({ jobId, onClose }: JobDetailDrawerProps) {
  const [job, setJob] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"analysis" | "info" | "description">("analysis");
  const { showToast } = useToast();

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      setError(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    getJobDetail(jobId)
      .then((data) => {
        if (isMounted) {
          setJob(data);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          setError(
            err instanceof Error
              ? err.message
              : `Failed to load details for job #${jobId}`
          );
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [jobId]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && jobId) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [jobId, onClose]);

  if (!jobId) return null;

  const handleReviewAction = async (status: "approved" | "rejected") => {
    if (!job) return;
    setActionLoading(true);
    try {
      await submitReview(job.id, status);
      setJob((prev) => (prev ? { ...prev, review_status: status } : null));
      showToast(
        `Job ${status === "approved" ? "Approved" : "Rejected"}`,
        `${job.title} at ${job.company}`,
        status === "approved" ? "success" : "info"
      );
    } catch (err: unknown) {
      showToast(
        "Action Failed",
        err instanceof Error ? err.message : "Failed to update review status",
        "error"
      );
    } finally {
      setActionLoading(false);
    }
  };

  const match = job?.match_details;

  return (
    <AnimatePresence>
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: "rgba(0, 0, 0, 0.75)",
          backdropFilter: "blur(6px)",
          WebkitBackdropFilter: "blur(6px)",
          zIndex: 50,
          display: "flex",
          justifyContent: "flex-end",
        }}
        onClick={onClose}
      >
        <motion.div
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", damping: 30, stiffness: 300 }}
          onClick={(e) => e.stopPropagation()}
          style={{
            width: "640px",
            maxWidth: "94vw",
            height: "100vh",
            backgroundColor: "rgba(13, 18, 29, 0.98)",
            borderLeft: "1px solid var(--border-medium)",
            boxShadow: "-10px 0 40px rgba(0, 0, 0, 0.7)",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: "20px 24px",
              borderBottom: "1px solid var(--border-subtle)",
              background: "rgba(19, 27, 46, 0.95)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              gap: "16px",
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                <span className="mono-text" style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                  JOB #{jobId}
                </span>
                {job && <ReviewStatusBadge status={job.review_status} />}
                {job?.has_application && (
                  <span
                    style={{
                      fontSize: "11px",
                      color: "var(--accent-light)",
                      background: "var(--accent-surface)",
                      border: "1px solid var(--border-glow)",
                      padding: "2px 7px",
                      borderRadius: "var(--radius-full)",
                      fontWeight: "600",
                    }}
                  >
                    Package Prepared
                  </span>
                )}
              </div>
              <h2 style={{ fontSize: "18px", fontWeight: "800", color: "var(--text-primary)", letterSpacing: "-0.01em" }}>
                {job ? job.title : "Loading opportunity details..."}
              </h2>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "4px", fontSize: "13px", color: "var(--text-secondary)" }}>
                <span style={{ fontWeight: "600" }}>{job?.company}</span>
                <span>•</span>
                <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <MapPin size={13} color="var(--text-muted)" />
                  <span>{job?.location || "Remote / Flexible"}</span>
                </div>
              </div>
            </div>

            <button
              onClick={onClose}
              style={{
                background: "var(--bg-surface-1)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-secondary)",
                width: "32px",
                height: "32px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
              }}
            >
              <X size={18} />
            </button>
          </div>

          {/* Navigation Tabs */}
          <div
            style={{
              padding: "0 24px",
              background: "var(--bg-surface-0)",
              borderBottom: "1px solid var(--border-subtle)",
              display: "flex",
              gap: "20px",
            }}
          >
            {[
              { id: "analysis", label: "AI Analysis" },
              { id: "info", label: "Metadata & Links" },
              { id: "description", label: "Job Description" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                style={{
                  padding: "12px 0",
                  background: "none",
                  border: "none",
                  borderBottom: activeTab === tab.id ? "2px solid var(--accent-primary)" : "2px solid transparent",
                  color: activeTab === tab.id ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: activeTab === tab.id ? "700" : "500",
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Drawer Body */}
          <div style={{ flex: 1, overflowY: "auto", padding: "24px", display: "flex", flexDirection: "column", gap: "24px" }}>
            {loading && (
              <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>
                Loading full detail snapshot...
              </div>
            )}

            {error && (
              <div className="glass-card" style={{ padding: "16px", borderColor: "var(--danger-border)", background: "var(--danger-surface)", color: "#fca5a5" }}>
                {error}
              </div>
            )}

            {job && !loading && (
              <>
                {/* Tab 1: AI Analysis */}
                {activeTab === "analysis" && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                    {/* Score & Recommendation Banner */}
                    <div
                      className="glass-card"
                      style={{
                        padding: "20px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        background: "linear-gradient(135deg, rgba(19, 27, 46, 0.9) 0%, rgba(26, 36, 61, 0.9) 100%)",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                        <ScoreRing score={job.match_score} size={54} strokeWidth={4.5} />
                        <div>
                          <div style={{ fontSize: "11px", fontWeight: "700", textTransform: "uppercase", color: "var(--text-muted)" }}>
                            AI Compatibility Score
                          </div>
                          <div style={{ fontSize: "14px", fontWeight: "700", color: "var(--text-primary)", marginTop: "2px" }}>
                            {job.match_score != null ? `${job.match_score}% Match` : "Not evaluated"}
                          </div>
                        </div>
                      </div>

                      <div>
                        <div style={{ fontSize: "11px", fontWeight: "700", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: "4px" }}>
                          Recommendation
                        </div>
                        <RecommendationBadge recommendation={job.recommendation} />
                      </div>
                    </div>

                    {/* Reasoning */}
                    {match?.reason && (
                      <div className="glass-card" style={{ padding: "18px" }}>
                        <div style={{ fontSize: "11px", fontWeight: "700", textTransform: "uppercase", color: "var(--text-secondary)", marginBottom: "6px" }}>
                          Ollama LLM Reasoning
                        </div>
                        <p style={{ fontSize: "13px", color: "var(--text-primary)", lineHeight: 1.6 }}>
                          {match.reason}
                        </p>
                      </div>
                    )}

                    {/* Strong Matches */}
                    {match?.strong_matches && match.strong_matches.length > 0 && (
                      <div>
                        <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--success)", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                          <CheckCircle size={14} />
                          <span>Strong Candidate Qualifications ({match.strong_matches.length})</span>
                        </div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                          {match.strong_matches.map((item, idx) => (
                            <span
                              key={idx}
                              style={{
                                fontSize: "12px",
                                padding: "4px 10px",
                                borderRadius: "var(--radius-sm)",
                                background: "var(--success-surface)",
                                border: "1px solid var(--success-border)",
                                color: "var(--success)",
                              }}
                            >
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Missing Requirements */}
                    {match?.minimum_requirements_missing && match.minimum_requirements_missing.length > 0 && (
                      <div>
                        <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--danger)", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                          <XCircle size={14} />
                          <span>Missing Requirements ({match.minimum_requirements_missing.length})</span>
                        </div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                          {match.minimum_requirements_missing.map((item, idx) => (
                            <span
                              key={idx}
                              style={{
                                fontSize: "12px",
                                padding: "4px 10px",
                                borderRadius: "var(--radius-sm)",
                                background: "var(--danger-surface)",
                                border: "1px solid var(--danger-border)",
                                color: "#f87171",
                              }}
                            >
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Concerns */}
                    {match?.concerns && match.concerns.length > 0 && (
                      <div>
                        <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--warning)", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                          <AlertTriangle size={14} />
                          <span>Potential Concerns ({match.concerns.length})</span>
                        </div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                          {match.concerns.map((item, idx) => (
                            <span
                              key={idx}
                              style={{
                                fontSize: "12px",
                                padding: "4px 10px",
                                borderRadius: "var(--radius-sm)",
                                background: "var(--warning-surface)",
                                border: "1px solid var(--warning-border)",
                                color: "#fbbf24",
                              }}
                            >
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 2: Metadata */}
                {activeTab === "info" && (
                  <div className="glass-card" style={{ padding: "20px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", fontSize: "13px" }}>
                    <div>
                      <div style={{ color: "var(--text-muted)", fontSize: "11px", textTransform: "uppercase" }}>Collector Source</div>
                      <div style={{ color: "var(--text-primary)", fontWeight: "600", marginTop: "2px" }}>{job.source}</div>
                    </div>
                    <div>
                      <div style={{ color: "var(--text-muted)", fontSize: "11px", textTransform: "uppercase" }}>External ID</div>
                      <div className="mono-text" style={{ color: "var(--text-primary)", marginTop: "2px" }}>{job.external_id}</div>
                    </div>
                    <div>
                      <div style={{ color: "var(--text-muted)", fontSize: "11px", textTransform: "uppercase" }}>Posted Date</div>
                      <div style={{ color: "var(--text-primary)", marginTop: "2px" }}>
                        {job.posted_at ? new Date(job.posted_at).toLocaleDateString() : "Not specified"}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: "var(--text-muted)", fontSize: "11px", textTransform: "uppercase" }}>Direct Job Listing</div>
                      <a
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-secondary"
                        style={{ padding: "6px 12px", fontSize: "12px", marginTop: "6px", display: "inline-flex" }}
                      >
                        <span>Open Posting</span>
                        <ExternalLink size={12} />
                      </a>
                    </div>
                  </div>
                )}

                {/* Tab 3: Description */}
                {activeTab === "description" && (
                  <div
                    className="glass-card"
                    style={{
                      padding: "20px",
                      maxHeight: "500px",
                      overflowY: "auto",
                      fontSize: "13px",
                      lineHeight: "1.6",
                      color: "var(--text-primary)",
                    }}
                  >
                    {job.description ? (
                      <div dangerouslySetInnerHTML={{ __html: job.description }} />
                    ) : (
                      <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "40px" }}>
                        No full description text available in database.
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Review Decision Actions Footer */}
          {job && (
            <div
              style={{
                padding: "16px 24px",
                background: "var(--bg-surface-0)",
                borderTop: "1px solid var(--border-subtle)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "12px",
              }}
            >
              <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                Current Status: <strong style={{ color: "var(--text-primary)" }}>{job.review_status}</strong>
              </div>

              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  onClick={() => handleReviewAction("rejected")}
                  disabled={actionLoading}
                  className="btn-danger"
                >
                  <XCircle size={15} />
                  <span>Reject Job</span>
                </button>
                <button
                  onClick={() => handleReviewAction("approved")}
                  disabled={actionLoading}
                  className="btn-success"
                >
                  <CheckCircle size={15} />
                  <span>Approve Job</span>
                </button>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

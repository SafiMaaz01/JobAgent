"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { JobDetail } from "@/lib/types";
import { submitReview, getReviewQueue } from "@/lib/api";
import ScoreRing from "@/components/ui/ScoreRing";
import { RecommendationBadge } from "./StatusBadge";
import { useToast } from "@/components/ui/Toast";
import {
  CheckCircle2,
  XCircle,
  ExternalLink,
  MapPin,
  Building2,
  Sparkles,
  AlertTriangle,
  Loader2,
  Check,
} from "lucide-react";

interface ReviewQueueClientProps {
  initialJobs: JobDetail[];
}

export default function ReviewQueueClient({ initialJobs }: ReviewQueueClientProps) {
  const [jobs, setJobs] = useState<JobDetail[]>(initialJobs);
  const [processingId, setProcessingId] = useState<number | null>(null);
  const { showToast } = useToast();

  const handleReviewAction = async (jobId: number, status: "approved" | "rejected") => {
    setProcessingId(jobId);
    try {
      const response = await submitReview(jobId, status);
      showToast(
        `Job #${jobId} ${status === "approved" ? "Approved" : "Rejected"}`,
        response.message || `Moved to ${status} state`,
        status === "approved" ? "success" : "info"
      );

      // Animate item out of local state
      setJobs((prev) => prev.filter((j) => j.id !== jobId));

      // Refresh authoritative queue from FastAPI backend
      const updatedQueue = await getReviewQueue();
      setJobs(updatedQueue);
    } catch (err: unknown) {
      showToast(
        "Action Failed",
        err instanceof Error ? err.message : `Failed to submit ${status} decision`,
        "error"
      );
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div>
      {jobs.length === 0 ? (
        <div
          className="glass-card"
          style={{
            padding: "60px 24px",
            textAlign: "center",
            background: "linear-gradient(135deg, rgba(19, 27, 46, 0.9) 0%, rgba(26, 36, 61, 0.9) 100%)",
          }}
        >
          <div
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "50%",
              background: "var(--success-surface)",
              border: "1px solid var(--success-border)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--success)",
              margin: "0 auto 16px auto",
            }}
          >
            <Check size={28} />
          </div>
          <div style={{ fontSize: "18px", fontWeight: "800", color: "var(--text-primary)" }}>
            Review Queue is Clear!
          </div>
          <div style={{ fontSize: "13.5px", color: "var(--text-muted)", marginTop: "6px", maxWidth: "480px", margin: "6px auto 0 auto" }}>
            All candidate match recommendations have been reviewed. Approved jobs are ready for application package preparation.
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ fontSize: "13px", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "8px" }}>
            <span>Awaiting manual decision:</span>
            <strong style={{ color: "var(--text-primary)" }}>{jobs.length} Job{jobs.length === 1 ? "" : "s"}</strong>
          </div>

          <AnimatePresence mode="popLayout">
            {jobs.map((job) => {
              const match = job.match_details;
              const isProcessing = processingId === job.id;

              return (
                <motion.div
                  key={job.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -100, scale: 0.95 }}
                  transition={{ duration: 0.25 }}
                  className="glass-card"
                  style={{
                    padding: "24px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "20px",
                  }}
                >
                  {/* Top Header */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      flexWrap: "wrap",
                      gap: "16px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "flex-start", gap: "14px" }}>
                      <ScoreRing score={job.match_score} size={52} strokeWidth={4} />
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                          <span className="mono-text" style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                            JOB #{job.id}
                          </span>
                          <span className="badge-semantic badge-pending">
                            Pending Review
                          </span>
                        </div>
                        <h2 style={{ fontSize: "18px", fontWeight: "800", color: "var(--text-primary)" }}>
                          {job.title}
                        </h2>
                        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "4px", fontSize: "13px", color: "var(--text-secondary)" }}>
                          <span style={{ fontWeight: "700", color: "var(--text-primary)" }}>{job.company}</span>
                          <span>•</span>
                          <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                            <MapPin size={13} color="var(--text-muted)" />
                            <span>{job.location || "Remote / Flexible"}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: "700", marginBottom: "4px", textAlign: "right" }}>
                        LLM Recommendation
                      </div>
                      <RecommendationBadge recommendation={job.recommendation} />
                    </div>
                  </div>

                  {/* AI Reasoning */}
                  {match?.reason && (
                    <div
                      style={{
                        background: "var(--bg-surface-0)",
                        border: "1px solid var(--border-subtle)",
                        borderRadius: "var(--radius-md)",
                        padding: "14px 16px",
                      }}
                    >
                      <div style={{ fontSize: "11px", fontWeight: "700", textTransform: "uppercase", color: "var(--accent-light)", marginBottom: "4px", display: "flex", alignItems: "center", gap: "6px" }}>
                        <Sparkles size={12} />
                        <span>Match Rationale</span>
                      </div>
                      <p style={{ fontSize: "13px", color: "var(--text-primary)", lineHeight: 1.6 }}>
                        {match.reason}
                      </p>
                    </div>
                  )}

                  {/* Candidate Match Breakdown */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "14px" }}>
                    {/* Strengths */}
                    {match?.strong_matches && match.strong_matches.length > 0 && (
                      <div style={{ background: "var(--bg-surface-0)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "14px" }}>
                        <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--success)", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                          <CheckCircle2 size={14} />
                          <span>Candidate Strengths ({match.strong_matches.length})</span>
                        </div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                          {match.strong_matches.map((item, idx) => (
                            <span
                              key={idx}
                              style={{
                                fontSize: "11.5px",
                                padding: "3px 8px",
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

                    {/* Missing */}
                    {match?.minimum_requirements_missing && match.minimum_requirements_missing.length > 0 && (
                      <div style={{ background: "var(--bg-surface-0)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "14px" }}>
                        <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--danger)", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                          <XCircle size={14} />
                          <span>Missing Requirements ({match.minimum_requirements_missing.length})</span>
                        </div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                          {match.minimum_requirements_missing.map((item, idx) => (
                            <span
                              key={idx}
                              style={{
                                fontSize: "11.5px",
                                padding: "3px 8px",
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
                  </div>

                  {/* Actions Footer */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      borderTop: "1px solid var(--border-subtle)",
                      paddingTop: "16px",
                    }}
                  >
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary"
                      style={{ padding: "6px 12px", fontSize: "12px" }}
                    >
                      <span>External Listing</span>
                      <ExternalLink size={12} />
                    </a>

                    {/* Single-item Deliberate Review Actions */}
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      <button
                        type="button"
                        disabled={isProcessing}
                        onClick={() => handleReviewAction(job.id, "rejected")}
                        className="btn-danger"
                      >
                        {isProcessing ? <Loader2 size={14} className="animate-spin" /> : <XCircle size={16} />}
                        <span>Reject</span>
                      </button>

                      <button
                        type="button"
                        disabled={isProcessing}
                        onClick={() => handleReviewAction(job.id, "approved")}
                        className="btn-success"
                      >
                        {isProcessing ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={16} />}
                        <span>Approve Job</span>
                      </button>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

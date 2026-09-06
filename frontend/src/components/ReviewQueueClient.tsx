"use client";

import { useState } from "react";
import { JobDetail } from "@/lib/types";
import { submitReview, getReviewQueue } from "@/lib/api";
import { MatchScoreBadge, RecommendationBadge } from "./StatusBadge";

interface ReviewQueueClientProps {
  initialJobs: JobDetail[];
}

export default function ReviewQueueClient({ initialJobs }: ReviewQueueClientProps) {
  const [jobs, setJobs] = useState<JobDetail[]>(initialJobs);
  const [processingId, setProcessingId] = useState<number | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleReviewAction = async (jobId: number, status: "approved" | "rejected") => {
    setProcessingId(jobId);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const response = await submitReview(jobId, status);
      setSuccessMessage(response.message || `Job #${jobId} successfully marked as ${status}.`);

      // Refresh the queue from real backend
      const updatedQueue = await getReviewQueue();
      setJobs(updatedQueue);
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : `Failed to submit ${status} decision for job #${jobId}`
      );
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div>
      {/* Notifications */}
      {successMessage && (
        <div
          style={{
            background: "var(--success-surface)",
            border: "1px solid rgba(16, 185, 129, 0.4)",
            color: "#6ee7b7",
            padding: "12px 16px",
            borderRadius: "var(--radius-lg)",
            marginBottom: "20px",
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
          <div className="error-title">Action Failed</div>
          <div>{errorMessage}</div>
        </div>
      )}

      {/* Empty State */}
      {jobs.length === 0 ? (
        <div className="table-container">
          <div className="empty-state">
            <div style={{ fontSize: "28px", marginBottom: "12px" }}>🎉</div>
            <div className="empty-state-title">Review queue is empty!</div>
            <div className="empty-state-desc">
              All recommended jobs have been reviewed. Check the Jobs Directory or Dashboard for approved listings.
            </div>
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            Showing <strong>{jobs.length}</strong> job{jobs.length === 1 ? "" : "s"} awaiting decision
          </div>

          {jobs.map((job) => {
            const match = job.match_details;
            const isProcessing = processingId === job.id;

            return (
              <div
                key={job.id}
                style={{
                  backgroundColor: "var(--bg-surface)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-lg)",
                  padding: "24px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "18px",
                  transition: "border-color 0.15s ease",
                }}
              >
                {/* Header Row */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    flexWrap: "wrap",
                    gap: "12px",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                        ID #{job.id}
                      </span>
                      <span
                        style={{
                          fontSize: "11px",
                          color: "var(--warning)",
                          background: "var(--warning-surface)",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          fontWeight: "600",
                          textTransform: "uppercase",
                        }}
                      >
                        Pending Decision
                      </span>
                    </div>

                    <h2 style={{ fontSize: "18px", fontWeight: "700", color: "var(--text-primary)" }}>
                      {job.title}
                    </h2>
                    <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "3px" }}>
                      <strong style={{ color: "var(--text-primary)" }}>{job.company}</strong> •{" "}
                      {job.location || "Remote / Not specified"}
                    </div>
                  </div>

                  {/* Score and Decision pills */}
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "3px" }}>
                        Match Score
                      </span>
                      <MatchScoreBadge score={job.match_score} />
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "3px" }}>
                        Recommendation
                      </span>
                      <RecommendationBadge recommendation={job.recommendation} />
                    </div>
                  </div>
                </div>

                {/* AI Reasoning Box */}
                {match?.reason && (
                  <div
                    style={{
                      backgroundColor: "var(--bg-subtle)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "var(--radius-md)",
                      padding: "14px 16px",
                    }}
                  >
                    <div style={{ fontSize: "11px", fontWeight: "600", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: "4px" }}>
                      AI Match Reasoning
                    </div>
                    <p style={{ fontSize: "13px", color: "var(--text-primary)", lineHeight: 1.5 }}>
                      {match.reason}
                    </p>
                  </div>
                )}

                {/* Match Details Lists */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "14px" }}>
                  {/* Strong Matches */}
                  {match?.strong_matches && match.strong_matches.length > 0 && (
                    <div style={{ backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", padding: "14px" }}>
                      <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--success)", marginBottom: "8px" }}>
                        ✓ Key Strengths ({match.strong_matches.length})
                      </div>
                      <div className="tag-list">
                        {match.strong_matches.map((item, idx) => (
                          <span key={idx} className="tag-item tag-item-strong">
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Missing Requirements */}
                  {match?.minimum_requirements_missing && match.minimum_requirements_missing.length > 0 && (
                    <div style={{ backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", padding: "14px" }}>
                      <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--danger)", marginBottom: "8px" }}>
                        ✕ Missing Requirements ({match.minimum_requirements_missing.length})
                      </div>
                      <div className="tag-list">
                        {match.minimum_requirements_missing.map((item, idx) => (
                          <span key={idx} className="tag-item tag-item-missing">
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Potential Concerns */}
                  {match?.concerns && match.concerns.length > 0 && (
                    <div style={{ backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", padding: "14px" }}>
                      <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--warning)", marginBottom: "8px" }}>
                        ⚠ Potential Concerns ({match.concerns.length})
                      </div>
                      <div className="tag-list">
                        {match.concerns.map((item, idx) => (
                          <span key={idx} className="tag-item tag-item-concern">
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions Row */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    borderTop: "1px solid var(--border-color)",
                    paddingTop: "16px",
                    marginTop: "6px",
                  }}
                >
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      fontSize: "13px",
                      color: "var(--brand-light)",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                    }}
                  >
                    View Job Posting ↗
                  </a>

                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <button
                      type="button"
                      disabled={isProcessing}
                      onClick={() => handleReviewAction(job.id, "rejected")}
                      style={{
                        padding: "8px 18px",
                        backgroundColor: "rgba(239, 68, 68, 0.15)",
                        border: "1px solid rgba(239, 68, 68, 0.4)",
                        borderRadius: "var(--radius-md)",
                        color: "#fca5a5",
                        fontSize: "13px",
                        fontWeight: "600",
                        cursor: isProcessing ? "not-allowed" : "pointer",
                        transition: "all 0.12s ease",
                      }}
                    >
                      {isProcessing ? "Processing..." : "✕ Reject"}
                    </button>

                    <button
                      type="button"
                      disabled={isProcessing}
                      onClick={() => handleReviewAction(job.id, "approved")}
                      style={{
                        padding: "8px 22px",
                        backgroundColor: "var(--success)",
                        border: "1px solid var(--success)",
                        borderRadius: "var(--radius-md)",
                        color: "#fff",
                        fontSize: "13px",
                        fontWeight: "600",
                        cursor: isProcessing ? "not-allowed" : "pointer",
                        boxShadow: "0 2px 8px rgba(16, 185, 129, 0.3)",
                        transition: "all 0.12s ease",
                      }}
                    >
                      {isProcessing ? "Processing..." : "✓ Approve for Application"}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

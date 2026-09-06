"use client";

import { useEffect, useState } from "react";
import { JobDetail } from "@/lib/types";
import { getJobDetail } from "@/lib/api";
import {
  MatchScoreBadge,
  RecommendationBadge,
  ReviewStatusBadge,
} from "./StatusBadge";

interface JobDetailDrawerProps {
  jobId: number | null;
  onClose: () => void;
}

export default function JobDetailDrawer({ jobId, onClose }: JobDetailDrawerProps) {
  const [job, setJob] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!jobId) return null;

  const match = job?.match_details;

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div className="drawer-header">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                ID #{jobId}
              </span>
              {job && <ReviewStatusBadge status={job.review_status} />}
              {job?.has_application && (
                <span
                  style={{
                    fontSize: "11px",
                    color: "var(--purple)",
                    background: "var(--purple-surface)",
                    padding: "2px 6px",
                    borderRadius: "4px",
                    fontWeight: "600",
                  }}
                >
                  Application Prepared
                </span>
              )}
            </div>
            <h2 style={{ fontSize: "18px", fontWeight: "700", color: "var(--text-primary)" }}>
              {job ? job.title : "Loading job..."}
            </h2>
            <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "2px" }}>
              {job ? `${job.company} • ${job.location || "Remote / Not specified"}` : ""}
            </div>
          </div>
          <button
            className="drawer-close-btn"
            onClick={onClose}
            aria-label="Close drawer"
          >
            ✕
          </button>
        </div>

        {/* Drawer Content */}
        <div className="drawer-content">
          {loading && (
            <div>
              <div className="skeleton" style={{ width: "100%", height: "90px", marginBottom: "16px" }} />
              <div className="skeleton" style={{ width: "100%", height: "160px", marginBottom: "16px" }} />
              <div className="skeleton" style={{ width: "100%", height: "240px" }} />
            </div>
          )}

          {error && (
            <div className="error-banner">
              <div className="error-title">Failed to load details</div>
              <div>{error}</div>
            </div>
          )}

          {job && !loading && (
            <>
              {/* Match Insights Banner */}
              <div>
                <div className="drawer-section-title">Match Assessment</div>
                <div className="insight-card">
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: "12px",
                      paddingBottom: "12px",
                      borderBottom: "1px solid var(--border-color)",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                        AI Score:
                      </span>
                      <MatchScoreBadge score={job.match_score} />
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                        Recommendation:
                      </span>
                      <RecommendationBadge recommendation={job.recommendation} />
                    </div>
                  </div>

                  {match?.reason && (
                    <div style={{ marginBottom: "14px" }}>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "4px", textTransform: "uppercase" }}>
                        Reasoning
                      </div>
                      <p style={{ fontSize: "13px", color: "var(--text-primary)", lineHeight: 1.5 }}>
                        {match.reason}
                      </p>
                    </div>
                  )}

                  {/* Strong Matches */}
                  {match?.strong_matches && match.strong_matches.length > 0 && (
                    <div style={{ marginBottom: "12px" }}>
                      <div style={{ fontSize: "11px", color: "var(--success)", marginBottom: "6px", fontWeight: "600" }}>
                        ✓ Strong Matches ({match.strong_matches.length})
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
                    <div style={{ marginBottom: "12px" }}>
                      <div style={{ fontSize: "11px", color: "var(--danger)", marginBottom: "6px", fontWeight: "600" }}>
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

                  {/* Concerns */}
                  {match?.concerns && match.concerns.length > 0 && (
                    <div style={{ marginBottom: "8px" }}>
                      <div style={{ fontSize: "11px", color: "var(--warning)", marginBottom: "6px", fontWeight: "600" }}>
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

                  {!match?.reason && !match?.strong_matches && (
                    <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                      Detailed matcher evaluation not yet generated for this listing.
                    </div>
                  )}
                </div>
              </div>

              {/* Quick Info & Links */}
              <div>
                <div className="drawer-section-title">Job Information</div>
                <div
                  style={{
                    background: "var(--bg-subtle)",
                    border: "1px solid var(--border-color)",
                    borderRadius: "var(--radius-lg)",
                    padding: "14px 16px",
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "12px",
                    fontSize: "12px",
                  }}
                >
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Source:</span>{" "}
                    <span style={{ color: "var(--text-primary)", fontWeight: "500" }}>
                      {job.source}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>External ID:</span>{" "}
                    <span style={{ color: "var(--text-primary)", fontFamily: "monospace" }}>
                      {job.external_id}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Posted:</span>{" "}
                    <span style={{ color: "var(--text-primary)" }}>
                      {job.posted_at ? new Date(job.posted_at).toLocaleDateString() : "Unknown"}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>External URL:</span>{" "}
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: "var(--brand-light)", fontWeight: "500" }}
                    >
                      Open Posting ↗
                    </a>
                  </div>
                </div>
              </div>

              {/* Full Description */}
              <div>
                <div className="drawer-section-title">Job Description</div>
                {job.description ? (
                  <div
                    className="job-description-box"
                    dangerouslySetInnerHTML={{ __html: job.description }}
                  />
                ) : (
                  <div className="job-description-box" style={{ color: "var(--text-muted)" }}>
                    No description text recorded in database.
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

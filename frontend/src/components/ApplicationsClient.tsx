"use client";

import { useState } from "react";
import Link from "next/link";
import { ApplicationSummary, JobSummary } from "@/lib/types";
import { prepareApplicationPackage, getApplications, getEligibleJobsForPreparation } from "@/lib/api";
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
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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
          <div className="error-title">Preparation Error</div>
          <div>{errorMessage}</div>
        </div>
      )}

      {/* Section 1: Prepared Application Packages */}
      <div>
        <div className="section-header">
          <div>
            <h2 className="section-title">Application Packages</h2>
            <p className="page-subtitle">
              Generated packages with candidate profile and saved question answers
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
                  <th style={{ width: "110px" }}>Created</th>
                  <th style={{ width: "150px", textAlign: "right" }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((app) => (
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
                            app.application_status === "applied"
                              ? "var(--purple-surface)"
                              : app.application_status === "ready_for_review"
                              ? "var(--success-surface)"
                              : "var(--bg-subtle)",
                          color:
                            app.application_status === "applied"
                              ? "var(--purple)"
                              : app.application_status === "ready_for_review"
                              ? "var(--success)"
                              : "var(--text-secondary)",
                          border:
                            app.application_status === "applied"
                              ? "1px solid rgba(139, 92, 246, 0.3)"
                              : "1px solid rgba(16, 185, 129, 0.3)",
                        }}
                      >
                        {app.application_status === "ready_for_review"
                          ? "Ready for Review"
                          : app.application_status === "applied"
                          ? "Submitted / Applied"
                          : app.application_status}
                      </span>
                    </td>
                    <td>
                      {app.has_resume ? (
                        <span style={{ fontSize: "12px", color: "var(--success)" }}>
                          ✓ PDF attached
                        </span>
                      ) : (
                        <span style={{ fontSize: "12px", color: "var(--danger)" }}>
                          ✕ Missing PDF
                        </span>
                      )}
                    </td>
                    <td style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                      {app.created_at ? app.created_at.split("T")[0] : "—"}
                    </td>

                    <td style={{ textAlign: "right" }}>
                      <Link
                        href={`/applications/${app.job_id}`}
                        style={{
                          background: "var(--brand-surface)",
                          border: "1px solid var(--brand)",
                          color: "var(--brand-light)",
                          borderRadius: "var(--radius-sm)",
                          padding: "5px 12px",
                          fontSize: "12px",
                          fontWeight: "600",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                        }}
                      >
                        Inspect Application →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Section 2: Approved Jobs Eligible for Package Preparation */}
      <div>
        <div className="section-header">
          <div>
            <h2 className="section-title">Approved Jobs Ready for Preparation</h2>
            <p className="page-subtitle">
              Jobs approved by user awaiting application package generation via authoritative Python module
            </p>
          </div>
          <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
            {eligibleJobs.length} approved job{eligibleJobs.length === 1 ? "" : "s"}
          </span>
        </div>

        {eligibleJobs.length === 0 ? (
          <div className="table-container">
            <div className="empty-state">
              <div className="empty-state-title">No approved jobs awaiting preparation</div>
              <div className="empty-state-desc">
                Visit the <Link href="/review" style={{ color: "var(--brand-light)", textDecoration: "underline" }}>Review Queue</Link> to approve matched opportunities.
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
                  <th style={{ width: "110px" }}>Review Status</th>
                  <th style={{ width: "130px" }}>Package State</th>
                  <th style={{ width: "180px", textAlign: "right" }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {eligibleJobs.map((job) => {
                  const isPreparing = preparingId === job.id;
                  const alreadyHasApp = job.has_application;

                  return (
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
                        {alreadyHasApp ? (
                          <span
                            style={{
                              fontSize: "11px",
                              color: "var(--success)",
                              background: "var(--success-surface)",
                              padding: "2px 6px",
                              borderRadius: "4px",
                            }}
                          >
                            ✓ Prepared
                          </span>
                        ) : (
                          <span
                            style={{
                              fontSize: "11px",
                              color: "var(--warning)",
                              background: "var(--warning-surface)",
                              padding: "2px 6px",
                              borderRadius: "4px",
                            }}
                          >
                            ● Needs Preparation
                          </span>
                        )}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <div style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
                          {alreadyHasApp ? (
                            <Link
                              href={`/applications/${job.id}`}
                              style={{
                                background: "var(--bg-subtle)",
                                border: "1px solid var(--border-color)",
                                borderRadius: "var(--radius-sm)",
                                padding: "4px 10px",
                                color: "var(--text-primary)",
                                fontSize: "12px",
                              }}
                            >
                              View Package
                            </Link>
                          ) : null}

                          <button
                            type="button"
                            disabled={isPreparing}
                            onClick={() => handlePreparePackage(job.id)}
                            style={{
                              background: "var(--brand)",
                              border: "1px solid var(--brand)",
                              borderRadius: "var(--radius-sm)",
                              color: "#fff",
                              padding: "5px 12px",
                              fontSize: "12px",
                              fontWeight: "600",
                              cursor: isPreparing ? "not-allowed" : "pointer",
                              opacity: isPreparing ? 0.7 : 1,
                            }}
                          >
                            {isPreparing
                              ? "Preparing..."
                              : alreadyHasApp
                              ? "Re-prepare"
                              : "Prepare Package"}
                          </button>
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
    </div>
  );
}

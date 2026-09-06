"use client";

import { useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { JobSummary } from "@/lib/types";
import {
  MatchScoreBadge,
  RecommendationBadge,
  ReviewStatusBadge,
} from "./StatusBadge";
import JobDetailDrawer from "./JobDetailDrawer";

interface JobsTableWithDrawerProps {
  jobs: JobSummary[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export default function JobsTableWithDrawer({
  jobs,
  total,
  page,
  limit,
  pages,
}: JobsTableWithDrawerProps) {
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const handlePageChange = (newPage: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", newPage.toString());
    router.push(`${pathname}?${params.toString()}`);
  };

  if (!jobs || jobs.length === 0) {
    return (
      <div className="table-container">
        <div className="empty-state">
          <div className="empty-state-title">No jobs found</div>
          <div className="empty-state-desc">
            Try adjusting your search criteria or clearing filters.
          </div>
        </div>
      </div>
    );
  }

  const startRecord = (page - 1) * limit + 1;
  const endRecord = Math.min(page * limit, total);

  return (
    <>
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: "80px" }}>Score</th>
              <th>Company</th>
              <th>Job Title</th>
              <th>Location</th>
              <th style={{ width: "110px" }}>Decision</th>
              <th style={{ width: "110px" }}>Status</th>
              <th style={{ width: "140px", textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr
                key={job.id}
                style={{ cursor: "pointer" }}
                onClick={() => setSelectedJobId(job.id)}
              >
                <td>
                  <MatchScoreBadge score={job.match_score} />
                </td>
                <td style={{ fontWeight: "600", color: "var(--text-primary)" }}>
                  {job.company}
                </td>
                <td>
                  <div style={{ fontWeight: "500" }}>{job.title}</div>
                  {job.has_application && (
                    <span
                      style={{
                        fontSize: "10px",
                        color: "var(--purple)",
                        display: "inline-block",
                        marginTop: "2px",
                      }}
                    >
                      ● Application prepared
                    </span>
                  )}
                </td>
                <td style={{ color: "var(--text-secondary)" }}>
                  {job.location || "Remote / Not specified"}
                </td>
                <td>
                  <RecommendationBadge recommendation={job.recommendation} />
                </td>
                <td>
                  <ReviewStatusBadge status={job.review_status} />
                </td>
                <td
                  style={{ textAlign: "right" }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <div style={{ display: "inline-flex", alignItems: "center", gap: "10px" }}>
                    <button
                      type="button"
                      onClick={() => setSelectedJobId(job.id)}
                      style={{
                        background: "var(--bg-subtle)",
                        border: "1px solid var(--border-color)",
                        borderRadius: "var(--radius-sm)",
                        padding: "3px 8px",
                        color: "var(--text-primary)",
                        fontSize: "11px",
                        fontWeight: "500",
                        cursor: "pointer",
                      }}
                    >
                      Details
                    </button>
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        color: "var(--brand-light)",
                        fontSize: "12px",
                      }}
                      title="Open external job board"
                    >
                      Posting ↗
                    </a>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination bar */}
        <div className="pagination-bar">
          <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
            Showing <strong style={{ color: "var(--text-primary)" }}>{startRecord}</strong> to{" "}
            <strong style={{ color: "var(--text-primary)" }}>{endRecord}</strong> of{" "}
            <strong style={{ color: "var(--text-primary)" }}>{total}</strong> jobs
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <button
              type="button"
              className="pagination-btn"
              disabled={page <= 1}
              onClick={() => handlePageChange(page - 1)}
            >
              ← Previous
            </button>
            <span style={{ fontSize: "12px", color: "var(--text-muted)", padding: "0 6px" }}>
              Page {page} of {pages}
            </span>
            <button
              type="button"
              className="pagination-btn"
              disabled={page >= pages}
              onClick={() => handlePageChange(page + 1)}
            >
              Next →
            </button>
          </div>
        </div>
      </div>

      {/* Slide-out Job Details Drawer */}
      <JobDetailDrawer
        jobId={selectedJobId}
        onClose={() => setSelectedJobId(null)}
      />
    </>
  );
}

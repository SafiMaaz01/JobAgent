"use client";

import React, { useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { JobSummary } from "@/lib/types";
import ScoreRing from "@/components/ui/ScoreRing";
import { RecommendationBadge, ReviewStatusBadge } from "./StatusBadge";
import JobDetailDrawer from "./JobDetailDrawer";
import { Building2, MapPin, ExternalLink, ChevronLeft, ChevronRight, Sparkles } from "lucide-react";

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
      <div className="glass-card" style={{ padding: "48px 24px", textAlign: "center", color: "var(--text-muted)" }}>
        <Sparkles size={28} style={{ margin: "0 auto 12px auto" }} />
        <div style={{ fontSize: "15px", fontWeight: "600", color: "var(--text-primary)" }}>
          No matching jobs found
        </div>
        <div style={{ fontSize: "13px", marginTop: "4px" }}>
          Try adjusting your search criteria or resetting filters.
        </div>
      </div>
    );
  }

  const startRecord = (page - 1) * limit + 1;
  const endRecord = Math.min(page * limit, total);

  return (
    <>
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: "70px", textAlign: "center" }}>Score</th>
              <th>Company & Role Title</th>
              <th>Location</th>
              <th style={{ width: "120px" }}>AI Rationale</th>
              <th style={{ width: "120px" }}>Status</th>
              <th style={{ width: "130px", textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr
                key={job.id}
                style={{ cursor: "pointer" }}
                onClick={() => setSelectedJobId(job.id)}
              >
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
                        {job.has_application && (
                          <span
                            style={{
                              fontSize: "10px",
                              color: "var(--accent-light)",
                              marginLeft: "8px",
                              fontWeight: "600",
                            }}
                          >
                            ● Application Package Ready
                          </span>
                        )}
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
                  <RecommendationBadge recommendation={job.recommendation} />
                </td>
                <td>
                  <ReviewStatusBadge status={job.review_status} />
                </td>
                <td style={{ textAlign: "right" }} onClick={(e) => e.stopPropagation()}>
                  <div style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
                    <button
                      type="button"
                      onClick={() => setSelectedJobId(job.id)}
                      className="btn-secondary"
                      style={{ padding: "5px 10px", fontSize: "11.5px" }}
                    >
                      Details
                    </button>
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary"
                      style={{ padding: "5px 8px", fontSize: "11.5px" }}
                      title="Open job listing"
                    >
                      <ExternalLink size={12} />
                    </a>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination bar */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "14px 18px",
            borderTop: "1px solid var(--border-subtle)",
            background: "var(--bg-surface-0)",
          }}
        >
          <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
            Showing <strong style={{ color: "var(--text-primary)" }}>{startRecord}</strong> to{" "}
            <strong style={{ color: "var(--text-primary)" }}>{endRecord}</strong> of{" "}
            <strong style={{ color: "var(--text-primary)" }}>{total.toLocaleString()}</strong> jobs
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <button
              type="button"
              className="btn-secondary"
              style={{ padding: "6px 12px", fontSize: "12px" }}
              disabled={page <= 1}
              onClick={() => handlePageChange(page - 1)}
            >
              <ChevronLeft size={14} />
              <span>Previous</span>
            </button>
            <span className="mono-text" style={{ fontSize: "12px", color: "var(--text-muted)", padding: "0 6px" }}>
              Page {page} of {pages}
            </span>
            <button
              type="button"
              className="btn-secondary"
              style={{ padding: "6px 12px", fontSize: "12px" }}
              disabled={page >= pages}
              onClick={() => handlePageChange(page + 1)}
            >
              <span>Next</span>
              <ChevronRight size={14} />
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

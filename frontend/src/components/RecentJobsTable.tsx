"use client";

import React from "react";
import { JobSummary } from "@/lib/types";
import ScoreRing from "@/components/ui/ScoreRing";
import { RecommendationBadge, ReviewStatusBadge } from "./StatusBadge";
import { MapPin, ExternalLink, Building2, Sparkles } from "lucide-react";

interface RecentJobsTableProps {
  jobs: JobSummary[];
  onSelectJob?: (job: JobSummary) => void;
}

export default function RecentJobsTable({ jobs, onSelectJob }: RecentJobsTableProps) {
  if (!jobs || jobs.length === 0) {
    return (
      <div className="data-table-container">
        <div style={{ padding: "48px 24px", textAlign: "center", color: "var(--text-muted)" }}>
          <Sparkles size={28} style={{ margin: "0 auto 12px auto", color: "var(--text-muted)" }} />
          <div style={{ fontSize: "15px", fontWeight: "600", color: "var(--text-primary)" }}>
            No top opportunities found
          </div>
          <div style={{ fontSize: "13px", marginTop: "4px" }}>
            No matched jobs available in the current query.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="data-table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th style={{ width: "70px", textAlign: "center" }}>Match</th>
            <th>Company & Role</th>
            <th>Location</th>
            <th style={{ width: "120px" }}>AI Rationale</th>
            <th style={{ width: "120px" }}>Status</th>
            <th style={{ width: "100px", textAlign: "right" }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr
              key={job.id}
              onClick={() => onSelectJob && onSelectJob(job)}
              style={{ cursor: onSelectJob ? "pointer" : "default" }}
            >
              <td style={{ textAlign: "center" }}>
                <ScoreRing score={job.match_score} size={40} strokeWidth={3.5} />
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
                <RecommendationBadge recommendation={job.recommendation} />
              </td>
              <td>
                <ReviewStatusBadge status={job.review_status} />
              </td>
              <td style={{ textAlign: "right" }} onClick={(e) => e.stopPropagation()}>
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary"
                  style={{ padding: "5px 10px", fontSize: "11.5px" }}
                >
                  <span>Listing</span>
                  <ExternalLink size={12} />
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

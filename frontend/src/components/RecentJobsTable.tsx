import { JobSummary } from "@/lib/types";
import {
  MatchScoreBadge,
  RecommendationBadge,
  ReviewStatusBadge,
} from "./StatusBadge";

interface RecentJobsTableProps {
  jobs: JobSummary[];
}

export default function RecentJobsTable({ jobs }: RecentJobsTableProps) {
  if (!jobs || jobs.length === 0) {
    return (
      <div className="table-container">
        <div className="empty-state">
          <div className="empty-state-title">No jobs available</div>
          <div className="empty-state-desc">
            No jobs have been collected or matched yet in the database.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th style={{ width: "80px" }}>Score</th>
            <th>Company</th>
            <th>Role Title</th>
            <th>Location</th>
            <th style={{ width: "110px" }}>Decision</th>
            <th style={{ width: "110px" }}>Status</th>
            <th style={{ width: "80px", textAlign: "right" }}>Source</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
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
              <td style={{ textAlign: "right" }}>
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: "var(--brand-light)",
                    fontSize: "12px",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "2px",
                  }}
                >
                  View ↗
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Badge components for visual status indicators across tables, cards, and drawers.
 * 
 * Provides color-coded badges for review status (pending, approved, applied, rejected),
 * match score ranges (high, medium, low), and recommendation directives (APPLY, PASS).
 */
interface StatusBadgeProps {
  status: string;
}


export function ReviewStatusBadge({ status }: StatusBadgeProps) {
  const normalized = (status || "pending").toLowerCase();
  let badgeClass = "badge-status-pending";

  if (normalized === "approved") {
    badgeClass = "badge-status-approved";
  } else if (normalized === "applied") {
    badgeClass = "badge-status-applied";
  } else if (normalized === "rejected") {
    badgeClass = "badge-status-rejected";
  }

  return <span className={`badge ${badgeClass}`}>{normalized}</span>;
}

interface MatchScoreBadgeProps {
  score: number | null | undefined;
}

export function MatchScoreBadge({ score }: MatchScoreBadgeProps) {
  if (score === null || score === undefined) {
    return <span className="badge badge-score badge-score-low">—</span>;
  }

  let badgeClass = "badge-score-low";
  if (score >= 80) {
    badgeClass = "badge-score-high";
  } else if (score >= 50) {
    badgeClass = "badge-score-mid";
  }

  return <span className={`badge badge-score ${badgeClass}`}>{score}%</span>;
}

interface RecommendationBadgeProps {
  recommendation: string | null | undefined;
}

export function RecommendationBadge({ recommendation }: RecommendationBadgeProps) {
  if (!recommendation) {
    return <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>—</span>;
  }

  const isApply = recommendation.toUpperCase() === "APPLY";
  return (
    <span
      className="badge"
      style={{
        backgroundColor: isApply ? "var(--success-surface)" : "rgba(100, 116, 139, 0.15)",
        color: isApply ? "var(--success)" : "var(--text-muted)",
        border: isApply ? "1px solid rgba(16, 185, 129, 0.3)" : "1px solid rgba(100, 116, 139, 0.25)",
      }}
    >
      {recommendation}
    </span>
  );
}

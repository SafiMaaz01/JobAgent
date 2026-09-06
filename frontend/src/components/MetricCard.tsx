interface MetricCardProps {
  label: string;
  value: number | string;
  subText?: string;
  badge?: string;
}

export default function MetricCard({
  label,
  value,
  subText,
  badge,
}: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="metric-label">
        <span>{label}</span>
        {badge && (
          <span
            style={{
              fontSize: "10px",
              padding: "2px 6px",
              borderRadius: "4px",
              backgroundColor: "var(--bg-subtle)",
              color: "var(--text-muted)",
            }}
          >
            {badge}
          </span>
        )}
      </div>
      <div className="metric-value">{value}</div>
      {subText && <div className="metric-sub">{subText}</div>}
    </div>
  );
}

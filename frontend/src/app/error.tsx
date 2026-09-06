"use client";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function DashboardError({ error, reset }: ErrorProps) {
  return (
    <div style={{ padding: "40px 0" }}>
      <div className="error-banner">
        <div className="error-title">Error Loading Dashboard</div>
        <p style={{ marginTop: "4px", fontSize: "13px" }}>{error.message}</p>
        <button
          onClick={() => reset()}
          style={{
            marginTop: "12px",
            padding: "6px 14px",
            backgroundColor: "rgba(239, 68, 68, 0.2)",
            border: "1px solid rgba(239, 68, 68, 0.4)",
            borderRadius: "var(--radius-sm)",
            color: "#fca5a5",
            cursor: "pointer",
            fontSize: "12px",
            fontWeight: "600",
          }}
        >
          Try Again
        </button>
      </div>
    </div>
  );
}

import { getReviewQueue } from "@/lib/api";
import { JobDetail } from "@/lib/types";
import ReviewQueueClient from "@/components/ReviewQueueClient";
import { CheckSquare, AlertTriangle } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function ReviewPage() {
  let jobs: JobDetail[] = [];
  let errorMessage: string | null = null;

  try {
    jobs = await getReviewQueue();
  } catch (err: unknown) {
    errorMessage =
      err instanceof Error
        ? err.message
        : "Failed to connect to JobAgent FastAPI server";
  }

  return (
    <div>
      {/* Header */}
      <div
        className="glass-card"
        style={{
          padding: "24px 28px",
          marginBottom: "24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "16px",
          background: "linear-gradient(135deg, rgba(19, 27, 46, 0.9) 0%, rgba(26, 36, 61, 0.9) 100%)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <h1 className="display-title">Human Review Queue</h1>
            <span className="badge-semantic badge-pending">
              <CheckSquare size={11} />
              <span>{jobs.length} Awaiting Review</span>
            </span>
          </div>
          <p className="caption-text" style={{ fontSize: "13.5px" }}>
            Deliberate human-in-the-loop decisions. Evaluate AI candidate match rationale and approve opportunities for package preparation.
          </p>
        </div>
      </div>

      {/* Error state */}
      {errorMessage && (
        <div
          className="glass-card"
          style={{
            padding: "18px 24px",
            marginBottom: "24px",
            borderColor: "var(--danger-border)",
            background: "var(--danger-surface)",
            color: "#fca5a5",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <AlertTriangle size={20} color="var(--danger)" />
            <div>
              <div style={{ fontWeight: "700" }}>Failed to load review queue</div>
              <div style={{ fontSize: "12px", marginTop: "2px" }}>{errorMessage}</div>
            </div>
          </div>
        </div>
      )}

      {/* Interactive Review Client */}
      {!errorMessage && <ReviewQueueClient initialJobs={jobs} />}
    </div>
  );
}

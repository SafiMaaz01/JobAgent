/**
 * Review Queue Page (Server Component).
 * 
 * Fetches all jobs recommended for application by the AI matcher that currently
 * await human review (status = 'pending'). Provides interactive approve/reject actions
 * through ReviewQueueClient.
 */
import { getReviewQueue } from "@/lib/api";
import { JobDetail } from "@/lib/types";
import ReviewQueueClient from "@/components/ReviewQueueClient";

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
      <div className="section-header" style={{ marginBottom: "20px" }}>
        <div>
          <h1 className="page-title">Review Queue</h1>
          <p className="page-subtitle">
            Evaluate high-scoring matched opportunities and approve them for application package preparation
          </p>
        </div>
      </div>

      {/* Error state */}
      {errorMessage && (
        <div className="error-banner">
          <div className="error-title">Failed to load review queue</div>
          <div>{errorMessage}</div>
        </div>
      )}

      {/* Interactive Review Client */}
      {!errorMessage && <ReviewQueueClient initialJobs={jobs} />}
    </div>
  );
}

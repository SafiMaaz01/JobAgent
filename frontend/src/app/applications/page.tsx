import { getApplications, getEligibleJobsForPreparation } from "@/lib/api";
import { ApplicationSummary, JobSummary } from "@/lib/types";
import ApplicationsClient from "@/components/ApplicationsClient";

export const dynamic = "force-dynamic";

export default async function ApplicationsPage() {
  let applications: ApplicationSummary[] = [];
  let eligibleJobs: JobSummary[] = [];
  let errorMessage: string | null = null;

  try {
    const [appsRes, eligibleRes] = await Promise.all([
      getApplications(),
      getEligibleJobsForPreparation(),
    ]);
    applications = appsRes;
    eligibleJobs = eligibleRes;
  } catch (err: unknown) {
    errorMessage =
      err instanceof Error
        ? err.message
        : "Failed to connect to JobAgent FastAPI server";
  }

  return (
    <div>
      {/* Header */}
      <div className="section-header" style={{ marginBottom: "24px" }}>
        <div>
          <h1 className="page-title">Applications Hub</h1>
          <p className="page-subtitle">
            Inspect prepared application packages, candidate data, and prepare packages for approved jobs
          </p>
        </div>
      </div>

      {/* Error state */}
      {errorMessage && (
        <div className="error-banner">
          <div className="error-title">Failed to load applications data</div>
          <div>{errorMessage}</div>
        </div>
      )}

      {/* Client List */}
      {!errorMessage && (
        <ApplicationsClient
          initialApplications={applications}
          initialEligibleJobs={eligibleJobs}
        />
      )}
    </div>
  );
}

import { getApplications, getEligibleJobsForPreparation } from "@/lib/api";
import { ApplicationSummary, JobSummary } from "@/lib/types";
import ApplicationsClient from "@/components/ApplicationsClient";
import { FileText, AlertTriangle } from "lucide-react";

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
      <div
        className="glass-card"
        style={{
          padding: "24px 28px",
          marginBottom: "28px",
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
            <h1 className="display-title">Applications Control Hub</h1>
            <span className="badge-semantic badge-ready">
              <FileText size={11} />
              <span>{applications.length} Packages Ready</span>
            </span>
          </div>
          <p className="caption-text" style={{ fontSize: "13.5px" }}>
            Candidate application packages, resolved QA answer pairs, generated resume PDFs, and Playwright automation launcher.
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
              <div style={{ fontWeight: "700" }}>Failed to load applications data</div>
              <div style={{ fontSize: "12px", marginTop: "2px" }}>{errorMessage}</div>
            </div>
          </div>
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

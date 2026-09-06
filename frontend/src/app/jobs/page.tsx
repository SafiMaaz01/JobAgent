import { getJobs, JobFilterParams } from "@/lib/api";
import JobsFilterBar from "@/components/JobsFilterBar";
import JobsTableWithDrawer from "@/components/JobsTableWithDrawer";
import { Briefcase, Sparkles, AlertTriangle } from "lucide-react";

export const dynamic = "force-dynamic";

interface JobsPageProps {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function JobsPage({ searchParams }: JobsPageProps) {
  const resolvedParams = await searchParams;

  const page = parseInt(
    typeof resolvedParams.page === "string" ? resolvedParams.page : "1",
    10
  );
  const limit = 20;

  const filterParams: JobFilterParams = {
    page: isNaN(page) || page < 1 ? 1 : page,
    limit,
    search:
      typeof resolvedParams.search === "string"
        ? resolvedParams.search
        : undefined,
    status:
      typeof resolvedParams.status === "string"
        ? resolvedParams.status
        : undefined,
    recommendation:
      typeof resolvedParams.recommendation === "string"
        ? resolvedParams.recommendation
        : undefined,
    min_score:
      typeof resolvedParams.min_score === "string"
        ? parseInt(resolvedParams.min_score, 10)
        : undefined,
    is_relevant:
      typeof resolvedParams.is_relevant === "string"
        ? parseInt(resolvedParams.is_relevant, 10)
        : undefined,
    sort_by: "match_score",
    sort_order: "desc",
  };

  let jobsData;
  let errorMessage: string | null = null;

  try {
    jobsData = await getJobs(filterParams);
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
            <h1 className="display-title">Jobs Intelligence Directory</h1>
            <span className="badge-semantic badge-ready">
              <Briefcase size={11} />
              <span>{jobsData ? `${jobsData.total.toLocaleString()} Total` : "Jobs Catalog"}</span>
            </span>
          </div>
          <p className="caption-text" style={{ fontSize: "13.5px" }}>
            Search, filter, and inspect collected opportunities, AI compatibility rationale, and application readiness.
          </p>
        </div>
      </div>

      {/* Filter toolbar */}
      <JobsFilterBar />

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
              <div style={{ fontWeight: "700" }}>Failed to load jobs</div>
              <div style={{ fontSize: "12px", marginTop: "2px" }}>{errorMessage}</div>
            </div>
          </div>
        </div>
      )}

      {/* Jobs table with Drawer */}
      {jobsData && (
        <JobsTableWithDrawer
          jobs={jobsData.items}
          total={jobsData.total}
          page={jobsData.page}
          limit={jobsData.limit}
          pages={jobsData.pages}
        />
      )}
    </div>
  );
}

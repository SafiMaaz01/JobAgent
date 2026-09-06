import { getJobs, JobFilterParams } from "@/lib/api";
import JobsFilterBar from "@/components/JobsFilterBar";
import JobsTableWithDrawer from "@/components/JobsTableWithDrawer";

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
      <div className="section-header" style={{ marginBottom: "20px" }}>
        <div>
          <h1 className="page-title">Jobs Directory</h1>
          <p className="page-subtitle">
            Search, filter, and inspect collected job opportunities and match evaluations
          </p>
        </div>
      </div>

      {/* Filter toolbar */}
      <JobsFilterBar />

      {/* Error state */}
      {errorMessage && (
        <div className="error-banner">
          <div className="error-title">Failed to load jobs</div>
          <div>{errorMessage}</div>
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

import { getDashboardStats, getRecentHighScoringJobs } from "@/lib/api";
import MetricCard from "@/components/MetricCard";
import RecentJobsTable from "@/components/RecentJobsTable";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let stats;
  let jobsData;
  let errorMessage: string | null = null;

  try {
    const [statsRes, jobsRes] = await Promise.all([
      getDashboardStats(),
      getRecentHighScoringJobs(10),
    ]);
    stats = statsRes;
    jobsData = jobsRes;
  } catch (err: unknown) {
    errorMessage =
      err instanceof Error
        ? err.message
        : "Failed to connect to JobAgent FastAPI server at http://127.0.0.1:8000";
  }

  return (
    <div>
      {/* Page Header */}
      <div className="section-header" style={{ marginBottom: "20px" }}>
        <div>
          <h1 className="page-title">Overview Dashboard</h1>
          <p className="page-subtitle">
            Live telemetry and pipeline metrics from local SQLite database
          </p>
        </div>
      </div>

      {/* Error State if Backend Unavailable */}
      {errorMessage && (
        <div className="error-banner">
          <div className="error-title">Backend Connection Error</div>
          <div>{errorMessage}</div>
          <div style={{ marginTop: "8px", fontSize: "12px", color: "var(--text-secondary)" }}>
            Ensure the FastAPI server is running: <code>python run_api.py</code>
          </div>
        </div>
      )}

      {/* KPI Metrics Grid */}
      {stats && (
        <div className="metrics-grid">
          <MetricCard
            label="Total Ingested"
            value={stats.total_jobs.toLocaleString()}
            subText="Greenhouse job boards"
            badge="DB"
          />
          <MetricCard
            label="Relevant Jobs"
            value={stats.relevant_jobs}
            subText="Filtered candidate matches"
            badge="Filter"
          />
          <MetricCard
            label="Pending Review"
            value={stats.pending_review}
            subText="Awaiting user decision"
            badge="Review"
          />
          <MetricCard
            label="Approved"
            value={stats.approved}
            subText="Ready for application prep"
            badge="Approved"
          />
          <MetricCard
            label="Ready Applications"
            value={stats.ready_applications}
            subText="Packages prepared in data/"
            badge="Apps"
          />
          <MetricCard
            label="Applied / Submitted"
            value={stats.applied}
            subText="Verified browser submissions"
            badge="Submitted"
          />
          <MetricCard
            label="Avg Match Score"
            value={`${stats.avg_match_score}%`}
            subText="AI evaluation average"
            badge="Score"
          />
        </div>
      )}

      {/* Recent High-Scoring Jobs Table */}
      <div style={{ marginTop: "32px" }}>
        <div className="section-header">
          <div>
            <h2 className="section-title">Top Matched & Recent Jobs</h2>
            <p className="page-subtitle">
              Ranked by AI match score from local evaluations
            </p>
          </div>
          {jobsData && (
            <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              Showing {jobsData.items.length} of {jobsData.total} jobs
            </span>
          )}
        </div>

        {jobsData ? (
          <RecentJobsTable jobs={jobsData.items} />
        ) : (
          !errorMessage && (
            <div className="table-container">
              <div className="empty-state">
                <div className="empty-state-title">Loading jobs...</div>
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
}

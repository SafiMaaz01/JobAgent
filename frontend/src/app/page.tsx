"use client";

import React, { useEffect, useState } from "react";
import { getDashboardStats, getRecentHighScoringJobs } from "@/lib/api";
import { DashboardStats, JobListResponse } from "@/lib/types";
import StatCard from "@/components/ui/StatCard";
import RecentJobsTable from "@/components/RecentJobsTable";
import DashboardCharts from "@/components/DashboardCharts";
import SystemStatusPanel from "@/components/SystemStatusPanel";
import Skeleton from "@/components/ui/Skeleton";
import { Sparkles, AlertTriangle, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [jobsData, setJobsData] = useState<JobListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadDashboardData() {
      try {
        const [statsRes, jobsRes] = await Promise.all([
          getDashboardStats(),
          getRecentHighScoringJobs(10),
        ]);
        if (isMounted) {
          setStats(statsRes);
          setJobsData(jobsRes);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setErrorMessage(
            err instanceof Error
              ? err.message
              : "Failed to connect to JobAgent FastAPI backend at http://127.0.0.1:8000"
          );
          setLoading(false);
        }
      }
    }
    loadDashboardData();
  }, []);

  return (
    <div>
      {/* Hero Command Center Header */}
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
            <h1 className="display-title">AI Operations Command Center</h1>
            <span className="badge-semantic badge-autofilling">
              <Sparkles size={11} />
              <span>Live SQLite State</span>
            </span>
          </div>
          <p className="caption-text" style={{ fontSize: "13.5px", maxWidth: "600px" }}>
            Autonomous job ingestion, Ollama LLM match evaluation, human-in-the-loop review, and Playwright application automation.
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px" }}>
          <Link href="/review" className="btn-primary">
            <span>Review Queue</span>
            {stats && stats.pending_review > 0 && (
              <span
                style={{
                  background: "#ffffff",
                  color: "var(--accent-primary)",
                  padding: "1px 7px",
                  borderRadius: "99px",
                  fontSize: "11px",
                  fontWeight: "800",
                }}
              >
                {stats.pending_review}
              </span>
            )}
            <ArrowRight size={14} />
          </Link>
          <Link href="/jobs" className="btn-secondary">
            <span>Jobs Directory</span>
          </Link>
        </div>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div
          className="glass-card"
          style={{
            padding: "18px 24px",
            marginBottom: "28px",
            borderColor: "var(--danger-border)",
            background: "var(--danger-surface)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px", color: "var(--danger)" }}>
            <AlertTriangle size={20} />
            <div>
              <div style={{ fontWeight: "700", fontSize: "14px" }}>Backend Connection Offline</div>
              <div style={{ fontSize: "12.5px", color: "#fca5a5", marginTop: "2px" }}>
                {errorMessage}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading Skeletons */}
      {loading && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(195px, 1fr))", gap: "16px", marginBottom: "28px" }}>
          {Array.from({ length: 7 }).map((_, i) => (
            <Skeleton key={i} height="110px" borderRadius="var(--radius-lg)" />
          ))}
        </div>
      )}

      {/* KPI Metrics Command Grid */}
      {stats && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(195px, 1fr))",
            gap: "16px",
            marginBottom: "28px",
          }}
        >
          <StatCard
            label="Total Ingested"
            value={stats.total_jobs.toLocaleString()}
            iconName="briefcase"
            subtext="Greenhouse & collectors"
            accentColor="indigo"
          />
          <StatCard
            label="Relevant Jobs"
            value={stats.relevant_jobs}
            iconName="target"
            subtext="Candidate skill match"
            accentColor="cyan"
          />
          <StatCard
            label="Pending Review"
            value={stats.pending_review}
            iconName="clock"
            subtext="Awaiting your approval"
            accentColor="amber"
          />
          <StatCard
            label="Approved Jobs"
            value={stats.approved}
            iconName="check"
            subtext="Ready for package prep"
            accentColor="emerald"
          />
          <StatCard
            label="Ready Packages"
            value={stats.ready_applications}
            iconName="file"
            subtext="JSON & QA answers ready"
            accentColor="purple"
          />
          <StatCard
            label="Submitted"
            value={stats.applied}
            iconName="send"
            subtext="Verified applications"
            accentColor="emerald"
          />
          <StatCard
            label="Avg Match Score"
            value={`${Math.round(stats.avg_match_score)}%`}
            iconName="sparkles"
            subtext="Ollama LLM score avg"
            accentColor="cyan"
          />
        </div>
      )}

      {/* Real Data Visualizations */}
      {stats && jobsData && (
        <DashboardCharts stats={stats} recentJobs={jobsData.items} />
      )}

      {/* Current System Status Panel */}
      {stats && <SystemStatusPanel stats={stats} />}

      {/* Top Opportunity Highlights Table */}
      <div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "16px",
          }}
        >
          <div>
            <h2 className="section-title">Top Matched Opportunities</h2>
            <p className="caption-text">
              Highest scoring jobs evaluated by local LLM
            </p>
          </div>
          {jobsData && (
            <Link href="/jobs" style={{ fontSize: "12.5px", color: "var(--accent-light)", fontWeight: "600" }}>
              View all {jobsData.total} jobs →
            </Link>
          )}
        </div>

        {jobsData ? (
          <RecentJobsTable jobs={jobsData.items} />
        ) : (
          !errorMessage && (
            <div className="glass-card" style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>
              Loading top opportunity matches...
            </div>
          )
        )}
      </div>
    </div>
  );
}

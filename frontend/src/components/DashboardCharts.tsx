"use client";

import React, { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import { DashboardStats, JobSummary } from "@/lib/types";

interface DashboardChartsProps {
  stats: DashboardStats;
  recentJobs: JobSummary[];
}

export default function DashboardCharts({ stats, recentJobs }: DashboardChartsProps) {
  const [hasMounted, setHasMounted] = useState(false);

  useEffect(() => {
    setHasMounted(true);
  }, []);

  // 1. Calculate Real Match Score Distribution from recent fetched jobs
  const scoreRanges = [
    { range: "90-100", label: "Excellent", count: 0, color: "#10b981" },
    { range: "75-89", label: "Strong", count: 0, color: "#06b6d4" },
    { range: "50-74", label: "Moderate", count: 0, color: "#f59e0b" },
    { range: "0-49", label: "Low", count: 0, color: "#ef4444" },
  ];

  recentJobs.forEach((job) => {
    const score = job.match_score ?? 0;
    if (score >= 90) scoreRanges[0].count++;
    else if (score >= 75) scoreRanges[1].count++;
    else if (score >= 50) scoreRanges[2].count++;
    else scoreRanges[3].count++;
  });

  // 2. Real Application Status Breakdown from authoritative DashboardStats
  const statusData = [
    { name: "Pending Review", value: stats.pending_review, color: "#f59e0b" },
    { name: "Approved", value: stats.approved, color: "#06b6d4" },
    { name: "Ready Packages", value: stats.ready_applications, color: "#10b981" },
    { name: "Submitted", value: stats.applied, color: "#818cf8" },
    { name: "Rejected", value: stats.rejected, color: "#ef4444" },
  ].filter((item) => item.value > 0);

  // 3. Real Job Source Breakdown calculated deterministically from fetched jobs
  const sourceCounts: Record<string, number> = {};
  recentJobs.forEach((job) => {
    const src = job.source || "unknown";
    sourceCounts[src] = (sourceCounts[src] || 0) + 1;
  });

  const sourceData = Object.entries(sourceCounts).map(([source, count]) => ({
    name: source,
    count,
  }));

  if (!hasMounted) {
    return (
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px", marginBottom: "28px" }}>
        <div className="glass-card" style={{ height: "260px", padding: "20px" }} />
        <div className="glass-card" style={{ height: "260px", padding: "20px" }} />
        <div className="glass-card" style={{ height: "260px", padding: "20px" }} />
      </div>
    );
  }

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
        gap: "20px",
        marginBottom: "28px",
      }}
    >
      {/* Chart 1: AI Match Score Distribution */}
      <div className="glass-card" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div className="section-title">Match Score Distribution</div>
            <div className="caption-text">Breakdown across recently ingested jobs</div>
          </div>
          <span
            className="mono-text"
            style={{
              fontSize: "11px",
              padding: "2px 8px",
              borderRadius: "var(--radius-sm)",
              background: "var(--accent-surface)",
              color: "var(--accent-light)",
            }}
          >
            Avg: {Math.round(stats.avg_match_score)}%
          </span>
        </div>

        <div style={{ width: "100%", height: "200px" }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={scoreRanges} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="range" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
              <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "rgba(13, 18, 29, 0.95)",
                  border: "1px solid var(--border-medium)",
                  borderRadius: "var(--radius-md)",
                  color: "var(--text-primary)",
                  fontSize: "12px",
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {scoreRanges.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 2: Application Pipeline Status */}
      <div className="glass-card" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
        <div>
          <div className="section-title">Application Lifecycle Breakdown</div>
          <div className="caption-text">Distribution of jobs across active pipeline states</div>
        </div>

        <div style={{ width: "100%", height: "200px", display: "flex", alignItems: "center" }}>
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(13, 18, 29, 0.95)",
                    border: "1px solid var(--border-medium)",
                    borderRadius: "var(--radius-md)",
                    color: "var(--text-primary)",
                    fontSize: "12px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ width: "100%", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
              No applications currently active in pipeline.
            </div>
          )}
        </div>
      </div>

      {/* Chart 3: Ingestion Source Breakdown */}
      <div className="glass-card" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
        <div>
          <div className="section-title">Ingestion Sources</div>
          <div className="caption-text">Job count per source collector</div>
        </div>

        <div style={{ width: "100%", height: "200px" }}>
          {sourceData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sourceData} layout="vertical" margin={{ top: 10, right: 10, left: 20, bottom: 0 }}>
                <XAxis type="number" stroke="var(--text-muted)" fontSize={11} tickLine={false} allowDecimals={false} />
                <YAxis dataKey="name" type="category" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(13, 18, 29, 0.95)",
                    border: "1px solid var(--border-medium)",
                    borderRadius: "var(--radius-md)",
                    color: "var(--text-primary)",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="count" fill="var(--accent-primary)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ width: "100%", textAlign: "center", color: "var(--text-muted)", fontSize: "13px", paddingTop: "70px" }}>
              No source breakdown available.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

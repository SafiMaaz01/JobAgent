"use client";

import React, { useEffect, useState } from "react";
import { Cpu, Server, CheckCircle2, Clock, PlayCircle, ShieldCheck } from "lucide-react";
import { getTaskStatus } from "@/lib/api";
import { DashboardStats, TaskStatus } from "@/lib/types";

interface SystemStatusPanelProps {
  stats: DashboardStats;
}

export default function SystemStatusPanel({ stats }: SystemStatusPanelProps) {
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function fetchTask() {
      try {
        const data = await getTaskStatus();
        if (isMounted) setTaskStatus(data);
      } catch {
        // Keep null if unavailable
      }
    }
    fetchTask();
    const interval = setInterval(fetchTask, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const systemStates = [
    {
      title: "FastAPI & SQLite Core",
      status: "Online & Authoritative",
      desc: `${stats.total_jobs.toLocaleString()} jobs stored locally`,
      icon: Server,
      color: "var(--success)",
    },
    {
      title: "Local Ollama LLM (qwen2.5:7b)",
      status: "Ready for Evaluation",
      desc: `Avg match score ${Math.round(stats.avg_match_score)}%`,
      icon: Cpu,
      color: "var(--accent-light)",
    },
    {
      title: "Human Review Safety Gate",
      status: stats.pending_review > 0 ? `${stats.pending_review} Jobs Pending Review` : "Queue Clear",
      desc: stats.pending_review > 0 ? "Requires manual approve/reject" : "All ingested jobs evaluated",
      icon: Clock,
      color: stats.pending_review > 0 ? "var(--warning)" : "var(--cyan-accent)",
    },
    {
      title: "Playwright Automation Runner",
      status: taskStatus ? taskStatus.status.toUpperCase() : "IDLE",
      desc: taskStatus?.message || "No active application autofill running",
      icon: taskStatus?.status === "running" ? PlayCircle : ShieldCheck,
      color: taskStatus?.status === "running" ? "var(--accent-light)" : "var(--text-secondary)",
    },
  ];

  return (
    <div className="glass-card" style={{ padding: "20px", marginBottom: "28px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
        <div>
          <div className="section-title">Current System & Automation Status</div>
          <div className="caption-text">Deterministic real-time status of backend services and execution runners</div>
        </div>
        <div className="badge-semantic badge-ready">
          <CheckCircle2 size={12} />
          <span>Real-time State</span>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "16px",
        }}
      >
        {systemStates.map((state, idx) => {
          const IconComp = state.icon;
          return (
            <div
              key={idx}
              style={{
                background: "var(--bg-surface-0)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "14px 16px",
                display: "flex",
                alignItems: "flex-start",
                gap: "12px",
              }}
            >
              <div
                style={{
                  width: "32px",
                  height: "32px",
                  borderRadius: "var(--radius-sm)",
                  background: "var(--bg-surface-1)",
                  border: "1px solid var(--border-subtle)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: state.color,
                  flexShrink: 0,
                }}
              >
                <IconComp size={16} />
              </div>
              <div>
                <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--text-primary)" }}>
                  {state.title}
                </div>
                <div style={{ fontSize: "12px", fontWeight: "600", color: state.color, marginTop: "2px" }}>
                  {state.status}
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                  {state.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

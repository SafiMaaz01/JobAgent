"use client";

import React from "react";
import {
  Clock,
  CheckCircle,
  XCircle,
  Send,
  AlertTriangle,
  Sparkles,
  Loader2,
  AlertCircle,
  FileCheck,
} from "lucide-react";

interface StatusBadgeProps {
  status: string;
  showIcon?: boolean;
}

export function ReviewStatusBadge({ status, showIcon = true }: StatusBadgeProps) {
  const normalized = (status || "pending").toLowerCase();

  let className = "badge-pending";
  let icon = <Clock size={12} />;
  let label = normalized;

  if (normalized === "approved") {
    className = "badge-approved";
    icon = <CheckCircle size={12} />;
  } else if (normalized === "ready" || normalized === "ready_applications") {
    className = "badge-ready";
    icon = <FileCheck size={12} />;
  } else if (normalized === "applied" || normalized === "submitted") {
    className = "badge-submitted";
    icon = <Send size={12} />;
    label = "submitted";
  } else if (normalized === "rejected") {
    className = "badge-rejected";
    icon = <XCircle size={12} />;
  } else if (normalized === "autofilling" || normalized === "running") {
    className = "badge-autofilling";
    icon = <Loader2 size={12} className="animate-spin" />;
  } else if (normalized === "waiting_for_confirmation" || normalized === "ready_to_submit") {
    className = "badge-waiting";
    icon = <AlertTriangle size={12} />;
    label = "ready to submit";
  } else if (normalized === "failed" || normalized === "error") {
    className = "badge-failed";
    icon = <AlertCircle size={12} />;
  }

  return (
    <span className={`badge-semantic ${className}`}>
      {showIcon && icon}
      <span>{label}</span>
    </span>
  );
}

interface MatchScoreBadgeProps {
  score: number | null | undefined;
}

export function MatchScoreBadge({ score }: MatchScoreBadgeProps) {
  if (score === null || score === undefined) {
    return (
      <span className="badge-semantic" style={{ background: "var(--bg-surface-1)", color: "var(--text-muted)", border: "1px solid var(--border-subtle)" }}>
        —
      </span>
    );
  }

  const rounded = Math.round(score);
  let bg = "rgba(100, 116, 139, 0.12)";
  let color = "#94a3b8";
  let border = "rgba(100, 116, 139, 0.25)";

  if (rounded >= 90) {
    bg = "rgba(16, 185, 129, 0.12)";
    color = "#10b981";
    border = "rgba(16, 185, 129, 0.3)";
  } else if (rounded >= 75) {
    bg = "rgba(6, 182, 212, 0.12)";
    color = "#06b6d4";
    border = "rgba(6, 182, 212, 0.3)";
  } else if (rounded >= 50) {
    bg = "rgba(245, 158, 11, 0.12)";
    color = "#f59e0b";
    border = "rgba(245, 158, 11, 0.3)";
  } else {
    bg = "rgba(239, 68, 68, 0.12)";
    color = "#ef4444";
    border = "rgba(239, 68, 68, 0.3)";
  }

  return (
    <span
      className="badge-semantic mono-text"
      style={{ background: bg, color, border, fontWeight: "800" }}
    >
      {rounded}%
    </span>
  );
}

interface RecommendationBadgeProps {
  recommendation: string | null | undefined;
}

export function RecommendationBadge({ recommendation }: RecommendationBadgeProps) {
  if (!recommendation) {
    return <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>—</span>;
  }

  const isApply = recommendation.toUpperCase() === "APPLY";
  return (
    <span
      className="badge-semantic"
      style={{
        backgroundColor: isApply ? "var(--success-surface)" : "rgba(100, 116, 139, 0.15)",
        color: isApply ? "var(--success)" : "var(--text-muted)",
        border: isApply ? "1px solid rgba(16, 185, 129, 0.3)" : "1px solid rgba(100, 116, 139, 0.25)",
      }}
    >
      {isApply && <Sparkles size={11} />}
      <span>{recommendation}</span>
    </span>
  );
}

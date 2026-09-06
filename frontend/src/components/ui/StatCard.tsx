"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  Briefcase,
  Target,
  Clock,
  CheckCircle2,
  FileCheck,
  Send,
  Sparkles,
  LucideIcon,
} from "lucide-react";

export type StatIconName =
  | "briefcase"
  | "target"
  | "clock"
  | "check"
  | "file"
  | "send"
  | "sparkles";

interface StatCardProps {
  label: string;
  value: string | number;
  iconName: StatIconName;
  subtext?: string;
  accentColor?: "indigo" | "emerald" | "amber" | "rose" | "cyan" | "purple";
}

const iconMap: Record<StatIconName, LucideIcon> = {
  briefcase: Briefcase,
  target: Target,
  clock: Clock,
  check: CheckCircle2,
  file: FileCheck,
  send: Send,
  sparkles: Sparkles,
};

export default function StatCard({
  label,
  value,
  iconName,
  subtext,
  accentColor = "indigo",
}: StatCardProps) {
  const IconComponent = iconMap[iconName] || Briefcase;

  const colorMap = {
    indigo: {
      bg: "rgba(99, 102, 241, 0.12)",
      border: "rgba(99, 102, 241, 0.25)",
      text: "#818cf8",
    },
    emerald: {
      bg: "rgba(16, 185, 129, 0.12)",
      border: "rgba(16, 185, 129, 0.25)",
      text: "#34d399",
    },
    amber: {
      bg: "rgba(245, 158, 11, 0.12)",
      border: "rgba(245, 158, 11, 0.25)",
      text: "#fbbf24",
    },
    rose: {
      bg: "rgba(239, 68, 68, 0.12)",
      border: "rgba(239, 68, 68, 0.25)",
      text: "#f87171",
    },
    cyan: {
      bg: "rgba(6, 182, 212, 0.12)",
      border: "rgba(6, 182, 212, 0.25)",
      text: "#38bdf8",
    },
    purple: {
      bg: "rgba(168, 85, 247, 0.12)",
      border: "rgba(168, 85, 247, 0.25)",
      text: "#c084fc",
    },
  };

  const scheme = colorMap[accentColor] || colorMap.indigo;

  return (
    <motion.div
      whileHover={{ y: -3, transition: { duration: 0.15 } }}
      className="glass-card"
      style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px", position: "relative", overflow: "hidden" }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: "11px", fontWeight: "700", textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-secondary)" }}>
          {label}
        </span>
        <div
          style={{
            width: "36px",
            height: "36px",
            borderRadius: "var(--radius-md)",
            backgroundColor: scheme.bg,
            border: `1px solid ${scheme.border}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: scheme.text,
          }}
        >
          <IconComponent size={18} strokeWidth={2} />
        </div>
      </div>

      <div>
        <div
          className="mono-text"
          style={{ fontSize: "28px", fontWeight: "800", color: "var(--text-primary)", letterSpacing: "-0.02em" }}
        >
          {value}
        </div>
        {subtext && (
          <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
            {subtext}
          </div>
        )}
      </div>

      <div
        style={{
          position: "absolute",
          top: "-20px",
          right: "-20px",
          width: "80px",
          height: "80px",
          borderRadius: "50%",
          background: scheme.bg,
          filter: "blur(24px)",
          pointerEvents: "none",
        }}
      />
    </motion.div>
  );
}

"use client";

import React from "react";
import { motion } from "framer-motion";

interface ScoreRingProps {
  score: number | null | undefined;
  size?: number;
  strokeWidth?: number;
  showLabel?: boolean;
}

export default function ScoreRing({
  score,
  size = 48,
  strokeWidth = 4,
  showLabel = true,
}: ScoreRingProps) {
  const numericScore = typeof score === "number" ? Math.round(score) : 0;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (numericScore / 100) * circumference;

  let color = "#94a3b8"; // low / default
  if (numericScore >= 90) color = "#10b981"; // excellent emerald
  else if (numericScore >= 75) color = "#06b6d4"; // strong cyan
  else if (numericScore >= 50) color = "#f59e0b"; // moderate amber
  else if (numericScore > 0) color = "#ef4444"; // low red

  return (
    <div
      style={{
        width: `${size}px`,
        height: `${size}px`,
        position: "relative",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        {/* Progress Arc */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          strokeLinecap="round"
        />
      </svg>
      {showLabel && (
        <span
          className="mono-text"
          style={{
            position: "absolute",
            fontSize: `${Math.max(10, size * 0.28)}px`,
            fontWeight: "800",
            color: score != null ? "var(--text-primary)" : "var(--text-muted)",
          }}
        >
          {score != null ? numericScore : "N/A"}
        </span>
      )}
    </div>
  );
}

"use client";

import React from "react";

interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
  height?: string | number;
  width?: string | number;
  borderRadius?: string;
}

export default function Skeleton({
  className = "",
  style = {},
  height = "16px",
  width = "100%",
  borderRadius = "var(--radius-sm)",
}: SkeletonProps) {
  return (
    <div
      className={className}
      style={{
        height: typeof height === "number" ? `${height}px` : height,
        width: typeof width === "number" ? `${width}px` : width,
        borderRadius,
        background: "linear-gradient(90deg, rgba(255, 255, 255, 0.03) 25%, rgba(255, 255, 255, 0.08) 50%, rgba(255, 255, 255, 0.03) 75%)",
        backgroundSize: "200% 100%",
        animation: "shimmer 1.8s infinite linear",
        ...style,
      }}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="glass-card" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
      <Skeleton width="40%" height="14px" />
      <Skeleton width="60%" height="28px" />
      <Skeleton width="80%" height="12px" />
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="data-table-container" style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "12px" }}>
      <Skeleton height="32px" width="100%" />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} height="40px" width="100%" />
      ))}
    </div>
  );
}

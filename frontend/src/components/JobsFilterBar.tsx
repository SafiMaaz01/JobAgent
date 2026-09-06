"use client";

import React, { useCallback, useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Search, RotateCcw, Loader2, Sparkles, Filter } from "lucide-react";

export default function JobsFilterBar() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const currentSearch = searchParams.get("search") || "";
  const currentStatus = searchParams.get("status") || "all";
  const currentRec = searchParams.get("recommendation") || "all";
  const currentMinScore = searchParams.get("min_score") || "0";
  const currentRelevant = searchParams.get("is_relevant") || "";

  const updateFilters = useCallback(
    (updates: Record<string, string | null>) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("page", "1");

      Object.entries(updates).forEach(([key, value]) => {
        if (value === null || value === "" || value === "all" || (key === "min_score" && value === "0")) {
          params.delete(key);
        } else {
          params.set(key, value);
        }
      });

      startTransition(() => {
        router.push(`${pathname}?${params.toString()}`);
      });
    },
    [pathname, router, searchParams]
  );

  const hasActiveFilters =
    currentSearch !== "" ||
    currentStatus !== "all" ||
    currentRec !== "all" ||
    currentMinScore !== "0" ||
    currentRelevant !== "";

  const handleClear = () => {
    startTransition(() => {
      router.push(pathname);
    });
  };

  return (
    <div
      className="glass-card"
      style={{
        padding: "16px 20px",
        marginBottom: "24px",
        display: "flex",
        flexDirection: "column",
        gap: "14px",
      }}
    >
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "12px" }}>
        {/* Search Input */}
        <div style={{ position: "relative", flex: 1, minWidth: "260px" }}>
          <Search
            size={16}
            color="var(--text-muted)"
            style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)" }}
          />
          <input
            type="text"
            className="input-field"
            placeholder="Search company, job title, or keywords..."
            style={{ paddingLeft: "36px" }}
            defaultValue={currentSearch}
            onChange={(e) => updateFilters({ search: e.target.value })}
          />
        </div>

        {/* Status Filter */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <Filter size={14} color="var(--text-muted)" />
          <select
            className="select-field"
            value={currentStatus}
            onChange={(e) => updateFilters({ status: e.target.value })}
          >
            <option value="all">All Statuses</option>
            <option value="pending">Pending Review</option>
            <option value="approved">Approved</option>
            <option value="applied">Applied / Submitted</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>

        {/* Recommendation Filter */}
        <select
          className="select-field"
          value={currentRec}
          onChange={(e) => updateFilters({ recommendation: e.target.value })}
        >
          <option value="all">All Recommendations</option>
          <option value="APPLY">Decision: APPLY</option>
          <option value="SKIP">Decision: SKIP</option>
        </select>

        {/* Minimum Match Score */}
        <select
          className="select-field"
          value={currentMinScore}
          onChange={(e) => updateFilters({ min_score: e.target.value })}
        >
          <option value="0">Any Match Score</option>
          <option value="50">Match ≥ 50%</option>
          <option value="75">Match ≥ 75%</option>
          <option value="90">Match ≥ 90%</option>
        </select>

        {/* Relevance Toggle */}
        <button
          type="button"
          className={`btn-secondary ${currentRelevant === "1" ? "btn-primary" : ""}`}
          style={{ padding: "8px 14px", fontSize: "12.5px" }}
          onClick={() =>
            updateFilters({ is_relevant: currentRelevant === "1" ? null : "1" })
          }
        >
          <Sparkles size={13} />
          <span>{currentRelevant === "1" ? "Relevant Only" : "Filter Relevant"}</span>
        </button>

        {/* Clear Filters */}
        {hasActiveFilters && (
          <button
            type="button"
            onClick={handleClear}
            className="btn-danger"
            style={{ padding: "8px 14px", fontSize: "12.5px" }}
          >
            <RotateCcw size={13} />
            <span>Reset</span>
          </button>
        )}

        {isPending && (
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", color: "var(--accent-light)" }}>
            <Loader2 size={14} className="animate-spin" />
            <span>Updating...</span>
          </div>
        )}
      </div>
    </div>
  );
}

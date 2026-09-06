"use client";

/**
 * Filter toolbar for the Jobs Directory.
 * 
 * Synchronizes search query, status dropdown, recommendation filter, and minimum score
 * directly to the URL query string so filtered views are bookmarkable and shareable.
 */
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useTransition } from "react";

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
      // Reset page to 1 on filter changes
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
    <div className="filters-toolbar">
      <div className="filters-row">
        {/* Search input */}
        <div className="search-input-wrapper">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="search-input"
            placeholder="Search company or job title..."
            defaultValue={currentSearch}
            onChange={(e) => updateFilters({ search: e.target.value })}
          />
        </div>

        {/* Status select */}
        <select
          className="filter-select"
          value={currentStatus}
          onChange={(e) => updateFilters({ status: e.target.value })}
        >
          <option value="all">All Statuses</option>
          <option value="pending">Pending Review</option>
          <option value="approved">Approved</option>
          <option value="applied">Applied</option>
          <option value="rejected">Rejected</option>
        </select>

        {/* Recommendation select */}
        <select
          className="filter-select"
          value={currentRec}
          onChange={(e) => updateFilters({ recommendation: e.target.value })}
        >
          <option value="all">All Recommendations</option>
          <option value="APPLY">Decision: APPLY</option>
          <option value="SKIP">Decision: SKIP</option>
        </select>

        {/* Minimum Match Score */}
        <select
          className="filter-select"
          value={currentMinScore}
          onChange={(e) => updateFilters({ min_score: e.target.value })}
        >
          <option value="0">Any Match Score</option>
          <option value="50">Score ≥ 50%</option>
          <option value="75">Score ≥ 75%</option>
          <option value="90">Score ≥ 90%</option>
        </select>

        {/* Relevance toggle */}
        <button
          type="button"
          className={`filter-btn ${currentRelevant === "1" ? "filter-btn-active" : ""}`}
          onClick={() =>
            updateFilters({ is_relevant: currentRelevant === "1" ? null : "1" })
          }
        >
          {currentRelevant === "1" ? "✓ Relevant Only" : "Relevant Only"}
        </button>

        {/* Clear Filters */}
        {hasActiveFilters && (
          <button
            type="button"
            onClick={handleClear}
            className="filter-btn"
            style={{ color: "var(--danger)" }}
          >
            Clear Filters
          </button>
        )}

        {isPending && (
          <span style={{ fontSize: "12px", color: "var(--brand-light)" }}>
            Updating...
          </span>
        )}
      </div>
    </div>
  );
}

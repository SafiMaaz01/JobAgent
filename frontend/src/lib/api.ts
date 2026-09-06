/**
 * JobAgent Frontend API Client.
 * 
 * Provides type-safe wrapper functions around the FastAPI REST API.
 * Uses native fetch with `cache: "no-store"` to ensure the UI always displays
 * real-time, authoritative SQLite state without stale client caching.
 */
import {
  ApplicationDetail,
  ApplicationSummary,
  DashboardStats,
  JobDetail,
  JobListResponse,
  JobSummary,
  PreparePackageResponse,
  TaskStatus,
  TaskActionResponse,
  Profile,
} from "./types";

// Base URL defaulting to local FastAPI instance
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * Generic HTTP fetch helper that handles JSON deserialization, error wrapping,
 * and cache invalidation.
 */
async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `API request failed: ${response.status} ${response.statusText} (${errorText})`
      );
    }

    return (await response.json()) as T;
  } catch (error: unknown) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error(`Network error connecting to JobAgent backend at ${url}`);
  }
}

/** Fetches dashboard KPI counts (total, relevant, pending, approved, applied, packages). */
export async function getDashboardStats(): Promise<DashboardStats> {
  return fetchJson<DashboardStats>("/api/stats");
}


export interface JobFilterParams {
  status?: string;
  recommendation?: string;
  is_relevant?: number;
  min_score?: number;
  search?: string;
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: string;
}

export async function getJobs(params?: JobFilterParams): Promise<JobListResponse> {
  const query = new URLSearchParams();
  if (params?.status && params.status !== "all") query.set("status", params.status);
  if (params?.recommendation && params.recommendation !== "all") {
    query.set("recommendation", params.recommendation);
  }
  if (params?.is_relevant !== undefined) {
    query.set("is_relevant", params.is_relevant.toString());
  }
  if (params?.min_score !== undefined && params.min_score > 0) {
    query.set("min_score", params.min_score.toString());
  }
  if (params?.search && params.search.trim()) {
    query.set("search", params.search.trim());
  }
  if (params?.page) query.set("page", params.page.toString());
  if (params?.limit) query.set("limit", params.limit.toString());
  if (params?.sort_by) query.set("sort_by", params.sort_by);
  if (params?.sort_order) query.set("sort_order", params.sort_order);

  const qs = query.toString();
  return fetchJson<JobListResponse>(`/api/jobs${qs ? `?${qs}` : ""}`);
}

export async function getRecentHighScoringJobs(limit = 10): Promise<JobListResponse> {
  return fetchJson<JobListResponse>(
    `/api/jobs?limit=${limit}&sort_by=match_score&sort_order=desc`
  );
}

export async function getJobDetail(id: number): Promise<JobDetail> {
  return fetchJson<JobDetail>(`/api/jobs/${id}`);
}

export async function getReviewQueue(): Promise<JobDetail[]> {
  return fetchJson<JobDetail[]>("/api/jobs/review/queue");
}

export async function submitReview(
  jobId: number,
  status: "approved" | "rejected" | "pending"
): Promise<{ id: number; review_status: string; reviewed_at?: string | null; message: string }> {
  return fetchJson<{ id: number; review_status: string; reviewed_at?: string | null; message: string }>(
    `/api/jobs/${jobId}/review`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status }),
    }
  );
}

export async function getApplications(): Promise<ApplicationSummary[]> {
  return fetchJson<ApplicationSummary[]>("/api/applications");
}

export async function getEligibleJobsForPreparation(): Promise<JobSummary[]> {
  return fetchJson<JobSummary[]>("/api/applications/eligible-jobs");
}

export async function getApplicationDetail(jobId: number): Promise<ApplicationDetail> {
  return fetchJson<ApplicationDetail>(`/api/applications/${jobId}`);
}

export async function prepareApplicationPackage(
  jobId: number
): Promise<PreparePackageResponse> {
  return fetchJson<PreparePackageResponse>(`/api/applications/${jobId}/prepare`, {
    method: "POST",
  });
}

export async function getTaskStatus(): Promise<TaskStatus> {
  return fetchJson<TaskStatus>("/api/tasks/status");
}

export async function startAutofill(jobId: number): Promise<TaskStatus> {
  return fetchJson<TaskStatus>(`/api/applications/${jobId}/autofill`, {
    method: "POST",
  });
}

export async function respondToTask(
  action: "confirm" | "cancel" | "input",
  value?: string
): Promise<TaskActionResponse> {
  return fetchJson<TaskActionResponse>("/api/tasks/respond", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ action, value }),
  });
}

export async function cancelTask(): Promise<TaskActionResponse> {
  return fetchJson<TaskActionResponse>("/api/tasks/cancel", {
    method: "POST",
  });
}

export async function getProfile(): Promise<Profile> {
  return fetchJson<Profile>("/api/config/profile");
}

export async function updateProfile(profile: Profile): Promise<Profile> {
  return fetchJson<Profile>("/api/config/profile", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(profile),
  });
}



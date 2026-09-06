import { DashboardStats, JobDetail, JobListResponse, TaskStatus } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

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

export async function getTaskStatus(): Promise<TaskStatus> {
  return fetchJson<TaskStatus>("/api/tasks/status");
}

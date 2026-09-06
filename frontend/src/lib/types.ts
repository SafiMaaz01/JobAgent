export interface DashboardStats {
  total_jobs: number;
  relevant_jobs: number;
  pending_review: number;
  approved: number;
  applied: number;
  rejected: number;
  ready_applications: number;
  total_application_packages: number;
  avg_match_score: number;
}

export interface JobSummary {
  id: number;
  source: string;
  external_id: string;
  company: string;
  title: string;
  location: string | null;
  url: string;
  posted_at: string | null;
  updated_at: string | null;
  is_relevant: number;
  match_score: number | null;
  recommendation: string | null;
  review_status: string;
  reviewed_at: string | null;
  applied_at: string | null;
  has_application: boolean;
}

export interface MatchDetails {
  match_score?: number;
  recommendation?: string;
  seniority_level?: string;
  employment_type?: string;
  location_match?: boolean;
  minimum_requirements_met?: string[];
  minimum_requirements_missing?: string[];
  strong_matches?: string[];
  concerns?: string[];
  reason?: string;
  [key: string]: unknown;
}

export interface JobDetail extends JobSummary {
  description?: string | null;
  matched_at?: string | null;
  match_details?: MatchDetails | null;
  application_status?: string | null;
}

export interface JobListResponse {
  items: JobSummary[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface TaskStatus {
  task: string | null;
  status: string;
  message: string;
  progress: number;
  details: Record<string, unknown> | null;
}

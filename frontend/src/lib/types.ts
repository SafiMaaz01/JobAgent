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

export interface AutomationTaskDetails {
  job_id?: number;
  company?: string;
  role?: string;
  stage?: string;
  verification_passed?: boolean | null;
  recent_logs?: string[];
  started_at?: string;
  updated_at?: string;
  input_prompt?: string;
  exit_code?: number;
  [key: string]: unknown;
}

export interface TaskStatus {
  task: string | null;
  status: string; // "idle" | "running" | "waiting_for_confirmation" | "waiting_for_input" | "completed" | "cancelled" | "error"
  message: string;
  progress: number;
  details: AutomationTaskDetails | null;
}

export interface TaskActionResponse {
  success: boolean;
  message: string;
}

export interface ReviewResponse {
  id: number;
  review_status: string;
  reviewed_at?: string | null;
  message: string;
}

export interface ApplicationSummary {
  job_id: number;
  company: string;
  title: string;
  location: string | null;
  match_score: number | null;
  recommendation: string | null;
  review_status?: string | null;
  application_status: string;
  has_resume: boolean;
  created_at: string | null;
  applied_at: string | null;
}

export interface ApplicationDetail {
  job_id: number;
  company: string;
  role: string;
  location: string | null;
  match_score: number | null;
  recommendation: string | null;
  review_status?: string | null;
  job_url: string;
  job_description?: string | null;
  application_status: string;
  resume_path?: string | null;
  resume_exists: boolean;
  resolved_answers: Record<string, unknown>;
  candidate?: Record<string, unknown> | null;
  match_details?: MatchDetails | null;
  automation_status: string;
  verification_status: string;
  verification_checks: Array<Record<string, unknown>>;
  submission_state: string;
  created_at?: string | null;
  applied_at?: string | null;
}

export interface PreparePackageResponse {
  job_id: number;
  status: string;
  message: string;
  package_file: string;
}

export interface EducationItem {
  degree: string;
  institution: string;
  start?: string;
  end?: string;
  graduation?: string;
  [key: string]: unknown;
}

export interface ExperienceItem {
  company: string;
  role: string;
  start?: string;
  end?: string;
  achievements?: string[];
  [key: string]: unknown;
}

export interface ApplicationPreferences {
  okay_with_five_day_office?: boolean;
  willing_to_relocate?: boolean;
  [key: string]: unknown;
}

export interface Profile {
  name: string;
  email: string;
  phone: string;
  location: string;
  target_roles: string[];
  skills: string[];
  years_of_experience: number;
  education: EducationItem[];
  preferred_locations: string[];
  remote_preference: string;
  minimum_salary: string;
  notice_period: string;
  work_authorization: string;
  application_preferences?: ApplicationPreferences | null;
  summary: string;
  experience: ExperienceItem[];
  projects?: Array<Record<string, unknown>>;
  github?: string | null;
  linkedin?: string | null;
  portfolio?: string | null;
  [key: string]: unknown;
}



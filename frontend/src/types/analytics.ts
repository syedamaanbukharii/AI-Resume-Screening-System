export interface DashboardStats {
  total_jobs: number;
  active_jobs: number;
  total_candidates: number;
  avg_score: number | null;
  funnel: Record<string, number>;
}

export interface JobAnalytics {
  job_id: string;
  score_distribution: { band: string; count: number }[];
  status_breakdown: Record<string, number>;
}

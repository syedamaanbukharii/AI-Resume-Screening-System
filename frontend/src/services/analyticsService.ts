import { apiFetch } from "@/lib/api";
import type { DashboardStats, JobAnalytics } from "@/types/analytics";

export function getDashboard(): Promise<DashboardStats> {
  return apiFetch<DashboardStats>("/api/v1/analytics/dashboard");
}

export function getJobAnalytics(jobId: string): Promise<JobAnalytics> {
  return apiFetch<JobAnalytics>(`/api/v1/analytics/jobs/${jobId}`);
}

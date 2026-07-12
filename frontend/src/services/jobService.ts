import { apiFetch } from "@/lib/api";
import type { Job, JobCreate, RankResult } from "@/types/job";

export function listJobs(status?: string): Promise<Job[]> {
  const q = status ? `?status=${status}` : "";
  return apiFetch<Job[]>(`/api/v1/jobs${q}`);
}

export function getJob(id: string): Promise<Job> {
  return apiFetch<Job>(`/api/v1/jobs/${id}`);
}

export function createJob(data: JobCreate): Promise<Job> {
  return apiFetch<Job>("/api/v1/jobs", { method: "POST", body: JSON.stringify(data) });
}

export function updateJob(id: string, data: Partial<JobCreate>): Promise<Job> {
  return apiFetch<Job>(`/api/v1/jobs/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

export function changeJobStatus(id: string, status: string): Promise<Job> {
  return apiFetch<Job>(`/api/v1/jobs/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function rankJob(id: string): Promise<RankResult> {
  return apiFetch<RankResult>(`/api/v1/jobs/${id}/rank`, { method: "POST" });
}

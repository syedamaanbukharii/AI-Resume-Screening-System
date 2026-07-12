import { apiFetch } from "@/lib/api";
import type {
  RankedCandidate,
  CandidateProfile,
  ResumeDetail,
  UploadResult,
  TaskStatus,
  InterviewQuestion,
  Report,
} from "@/types/candidate";

export function listRankedCandidates(jobId: string): Promise<RankedCandidate[]> {
  return apiFetch<RankedCandidate[]>(`/api/v1/jobs/${jobId}/candidates`);
}

export function getCandidateForJob(
  jobId: string,
  candidateId: string,
): Promise<RankedCandidate> {
  return apiFetch<RankedCandidate>(`/api/v1/jobs/${jobId}/candidates/${candidateId}`);
}

export function getCandidate(id: string): Promise<CandidateProfile> {
  return apiFetch<CandidateProfile>(`/api/v1/candidates/${id}`);
}

export function updateCandidateStatus(
  jobId: string,
  candidateId: string,
  status: string,
): Promise<RankedCandidate> {
  return apiFetch<RankedCandidate>(
    `/api/v1/jobs/${jobId}/candidates/${candidateId}/status`,
    { method: "PATCH", body: JSON.stringify({ status }) },
  );
}

export function updateCandidateNotes(
  jobId: string,
  candidateId: string,
  notes: string,
): Promise<RankedCandidate> {
  return apiFetch<RankedCandidate>(
    `/api/v1/jobs/${jobId}/candidates/${candidateId}/notes`,
    { method: "PUT", body: JSON.stringify({ notes }) },
  );
}

export function listResumes(jobId: string): Promise<ResumeDetail[]> {
  return apiFetch<ResumeDetail[]>(`/api/v1/jobs/${jobId}/resumes`);
}

export function uploadResumes(jobId: string, files: File[]): Promise<UploadResult[]> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  return apiFetch<UploadResult[]>(`/api/v1/jobs/${jobId}/resumes`, {
    method: "POST",
    body: form,
  });
}

export function getTask(taskId: string): Promise<TaskStatus> {
  return apiFetch<TaskStatus>(`/api/v1/tasks/${taskId}`);
}

export function getQuestions(
  jobId: string,
  candidateId: string,
): Promise<InterviewQuestion[]> {
  return apiFetch<InterviewQuestion[]>(
    `/api/v1/jobs/${jobId}/candidates/${candidateId}/questions`,
  );
}

export function getReport(jobId: string, candidateId: string): Promise<Report> {
  return apiFetch<Report>(`/api/v1/jobs/${jobId}/candidates/${candidateId}/report`);
}

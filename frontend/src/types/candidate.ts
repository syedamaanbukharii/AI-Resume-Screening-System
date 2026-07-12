export interface RankedCandidate {
  candidate_id: string;
  job_id: string;
  resume_id: string;
  overall_score: number | null;
  skill_score: number | null;
  experience_score: number | null;
  education_score: number | null;
  semantic_score: number | null;
  certification_score: number | null;
  status: string;
  recruiter_notes: string | null;
}

export interface CandidateProfile {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
}

export interface ResumeDetail {
  id: string;
  job_id: string;
  candidate_id: string | null;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  parsing_status: "pending" | "processing" | "completed" | "failed";
  parsing_error: string | null;
  parsed_profile: Record<string, unknown> | null;
}

export interface UploadResult {
  resume_id: string;
  task_id: string;
  filename: string;
  status: string;
}

export interface TaskStatus {
  id: string;
  task_type: string;
  reference_id: string;
  status: string;
  error_message: string | null;
}

export interface InterviewQuestion {
  id: string;
  category: string;
  difficulty: string;
  question: string;
  expected_answer: string | null;
  evaluation_criteria: string | null;
}

export interface Report {
  id: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  recommendation: string | null;
  risk_factors: string[];
  interview_plan: string | null;
  model_used: string | null;
}

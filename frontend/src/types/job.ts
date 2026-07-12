export interface Job {
  id: string;
  title: string;
  department: string | null;
  description_raw: string;
  required_skills: string[];
  preferred_skills: string[];
  min_experience_years: number | null;
  education_level: string | null;
  status: "draft" | "active" | "closed" | "archived";
  created_by: string | null;
}

export interface JobCreate {
  title: string;
  description_raw: string;
  department?: string | null;
  required_skills?: string[];
  preferred_skills?: string[];
  min_experience_years?: number | null;
  education_level?: string | null;
}

export interface RankResult {
  job_id: string;
  ranked_count: number;
  top_candidate_id: string | null;
  top_score: number | null;
}

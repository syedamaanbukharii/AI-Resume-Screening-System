/** Candidate pipeline statuses, in funnel order. */
export const CANDIDATE_STATUSES = [
  "new",
  "screened",
  "shortlisted",
  "interview",
  "rejected",
  "hired",
] as const;

export type CandidateStatus = (typeof CANDIDATE_STATUSES)[number];

/** Job lifecycle statuses. */
export const JOB_STATUSES = ["draft", "active", "closed", "archived"] as const;
export type JobStatus = (typeof JOB_STATUSES)[number];

/** Display labels for the five scoring factors. */
export const SCORE_FACTORS = [
  { key: "skill_score", label: "Skills" },
  { key: "experience_score", label: "Experience" },
  { key: "education_score", label: "Education" },
  { key: "semantic_score", label: "Semantic" },
  { key: "certification_score", label: "Certs" },
] as const;

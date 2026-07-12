"""Prompt for structured extraction of a job description."""

from __future__ import annotations

SYSTEM_PROMPT = """You extract structured requirements from a job description. \
Return ONLY a JSON object, no prose, no markdown fences. Extract only what is \
stated; use null or empty lists when absent. Schema:

{
  "required_skills": string[],
  "preferred_skills": string[],
  "min_experience_years": integer | null,
  "education_level": string | null,
  "field": string | null,
  "responsibilities": string[]
}

Rules:
- required_skills: must-haves. preferred_skills: nice-to-haves.
- min_experience_years: integer years if stated, else null.
- education_level: e.g. "bachelor", "master", null if unspecified.
- field: the primary domain (e.g. "computer science", "data engineering").
- Deduplicate and keep skill entries concise.
"""


def build_user_prompt(jd_text: str) -> str:
    """Wrap raw JD text as the user turn for extraction."""
    return f"Job description:\n\n{jd_text}\n\nReturn the JSON object now."

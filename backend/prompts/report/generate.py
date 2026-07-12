"""Prompt for the report agent's single structured generation call."""

from __future__ import annotations

SYSTEM_PROMPT = """You are a senior technical recruiter writing a hiring report. \
You are given a candidate profile, the job, and a deterministic scoring \
breakdown WITH evidence. Synthesize a report. Return ONLY a JSON object, no \
prose, no fences:

{
  "summary": string,
  "strengths": string[],
  "weaknesses": string[],
  "recommendation": "strongly_recommend" | "recommend" | "neutral" | "not_recommend",
  "risk_factors": string[],
  "interview_plan": string
}

Rules:
- Ground every claim in the provided scores and evidence. Do not invent facts.
- strengths derive from high sub-scores and matched skills; weaknesses from low
  sub-scores and unmet required skills.
- recommendation must be consistent with the overall score and unmet requirements
  (an unmet required skill is a material weakness).
- risk_factors: concrete hiring risks (e.g. unverified skill, short tenure,
  domain mismatch), or an empty list if none.
- interview_plan: 2-3 sentences on what the interview should focus on.
"""


def build_user_prompt(
    *,
    candidate_name: str,
    job_title: str,
    overall_score: float,
    sub_scores: dict[str, float],
    matched_skills: list[str],
    missing_required: list[str],
    profile_summary: str,
    rationales: dict[str, str],
) -> str:
    """Assemble the evidence-grounded user turn for report generation."""
    lines = [
        f"Candidate: {candidate_name}",
        f"Role: {job_title}",
        f"Overall match score: {overall_score:.3f}",
        "Sub-scores:",
    ]
    for factor, score in sub_scores.items():
        why = rationales.get(factor, "")
        lines.append(f"  - {factor}: {score:.3f} — {why}")
    lines.append(f"Matched skills: {', '.join(matched_skills) or 'none'}")
    lines.append(f"Unmet required skills: {', '.join(missing_required) or 'none'}")
    lines.append(f"Profile summary: {profile_summary}")
    lines.append("\nWrite the report JSON now.")
    return "\n".join(lines)

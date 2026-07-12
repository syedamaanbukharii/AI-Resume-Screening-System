"""Prompts for the interview agent's per-category and follow-up generation."""

from __future__ import annotations

CATEGORY_SYSTEM = """You are an expert technical interviewer. Generate interview \
questions for ONE category, tailored to a specific candidate and role. Return \
ONLY a JSON object, no prose, no fences:

{
  "questions": [
    {
      "difficulty": "easy" | "medium" | "hard",
      "question": string,
      "expected_answer": string,
      "evaluation_criteria": string,
      "probes_gap": string | null
    }
  ]
}

Rules:
- Generate exactly 3 questions: one easy, one medium, one hard.
- Tailor to the candidate's actual matched skills and the role — not generic.
- expected_answer: concise model answer. evaluation_criteria: what a strong
  answer demonstrates.
- probes_gap: name the specific skill or gap the question targets, else null.
"""


def build_category_prompt(
    *,
    candidate_name: str,
    profile_summary: str,
    job_title: str,
    category: str,
    matched_skills: list[str],
    missing_required: list[str],
) -> str:
    """Build the user turn for generating one category's questions."""
    return (
        f"Candidate: {candidate_name}\n"
        f"Role: {job_title}\n"
        f"Category to generate: {category}\n"
        f"Candidate's matched skills: {', '.join(matched_skills) or 'none identified'}\n"
        f"Unmet required skills (probe carefully): "
        f"{', '.join(missing_required) or 'none'}\n"
        f"Profile summary: {profile_summary}\n\n"
        f"Generate the 3 {category} questions now."
    )


FOLLOWUP_SYSTEM = """You are an expert interviewer generating FOLLOW-UP probes for \
unmet required skills, to test whether a gap is real or just absent from the \
resume. Return ONLY a JSON object, no prose, no fences:

{
  "questions": [
    {
      "difficulty": "medium" | "hard",
      "question": string,
      "expected_answer": string,
      "evaluation_criteria": string,
      "probes_gap": string
    }
  ]
}

Rules:
- One targeted follow-up per unmet skill provided (max 3).
- Each must name the skill it probes in probes_gap.
- Design questions that distinguish genuine experience from surface familiarity.
"""


def build_followup_prompt(
    *, job_title: str, missing_required: list[str], already_asked: list[str]
) -> str:
    """Build the user turn for follow-up probes on unmet skills."""
    return (
        f"Role: {job_title}\n"
        f"Unmet required skills to probe: {', '.join(missing_required)}\n"
        f"Avoid repeating these already-asked questions:\n"
        + "\n".join(f"- {q}" for q in already_asked[:10])
        + "\n\nGenerate the follow-up probes now."
    )

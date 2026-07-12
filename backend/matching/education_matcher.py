"""Education matching: degree-level ranking + field alignment."""

from __future__ import annotations

from backend.matching.schemas import EducationScore
from backend.resume.schemas import EducationEntry

# Ordinal ranking of degree levels. Higher satisfies lower.
_DEGREE_RANK: dict[str, int] = {
    "high school": 1,
    "diploma": 2,
    "associate": 3,
    "bachelor": 4,
    "bachelor of science": 4,
    "bachelor of technology": 4,
    "bachelor of engineering": 4,
    "bachelor of arts": 4,
    "master": 5,
    "master of science": 5,
    "master of technology": 5,
    "master of business administration": 5,
    "doctor of philosophy": 6,
    "phd": 6,
    "doctorate": 6,
}


def _rank_for(text: str | None) -> int:
    """Return the ordinal rank for a degree/level string (0 if unknown)."""
    if not text:
        return 0
    key = text.strip().lower()
    if key in _DEGREE_RANK:
        return _DEGREE_RANK[key]
    for name, rank in sorted(_DEGREE_RANK.items(), key=lambda kv: -len(kv[0])):
        if name in key:
            return rank
    return 0


def score_education(
    *,
    education: list[EducationEntry],
    required_level: str | None,
    job_field_terms: list[str] | None = None,
) -> EducationScore:
    """Score a candidate's education against the JD's required level and field.

    Score combines level satisfaction (0.7 weight) and field alignment
    (0.3 weight). If no level is required, education is treated as satisfied
    but field alignment still contributes as a small bonus signal.

    Args:
        education: Candidate education entries (degrees normalized upstream).
        required_level: JD's required degree level, or None.
        job_field_terms: Field keywords from the JD for alignment (e.g.
            ["computer science", "engineering"]).

    Returns:
        An EducationScore in [0, 1] with rationale.
    """
    highest = None
    highest_rank = 0
    for entry in education:
        r = _rank_for(entry.degree)
        if r > highest_rank:
            highest_rank = r
            highest = entry.degree

    field_terms = [t.lower() for t in (job_field_terms or [])]
    field_aligned = False
    if field_terms:
        for entry in education:
            hay = f"{entry.field or ''} {entry.degree}".lower()
            if any(term in hay for term in field_terms):
                field_aligned = True
                break

    if required_level is None:
        base = 1.0 if highest_rank > 0 else 0.6
        field_bonus = 0.0 if not field_terms else (0.0 if field_aligned else -0.1)
        score = max(min(base + field_bonus, 1.0), 0.0)
        rationale = (
            f"No degree level required; highest held: {highest or 'unknown'}."
            + (" Field aligned." if field_aligned else "")
        )
        return EducationScore(
            score=round(score, 4),
            highest_degree=highest,
            required_level=None,
            field_aligned=field_aligned,
            rationale=rationale,
        )

    required_rank = _rank_for(required_level)
    if required_rank == 0:
        level_score = 1.0 if highest_rank > 0 else 0.5
    elif highest_rank >= required_rank:
        level_score = 1.0
    else:
        level_score = round(highest_rank / required_rank, 4) if required_rank else 0.0

    field_score = 1.0 if (field_aligned or not field_terms) else 0.4
    score = round(0.7 * level_score + 0.3 * field_score, 4)
    rationale = (
        f"Highest degree {highest or 'unknown'} vs required {required_level}: "
        f"level {level_score:.0%}"
        + (", field aligned" if field_aligned else (", field not aligned" if field_terms else ""))
        + "."
    )
    return EducationScore(
        score=score,
        highest_degree=highest,
        required_level=required_level,
        field_aligned=field_aligned,
        rationale=rationale,
    )

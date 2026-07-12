"""Experience matching: saturating score against required years."""

from __future__ import annotations

from backend.matching.schemas import ExperienceScore


def score_experience(
    *, candidate_years: float | None, required_years: int | None
) -> ExperienceScore:
    """Score candidate experience against the JD's minimum.

    Uses a saturating ratio: full credit at or above the requirement, linear
    below it. Experience beyond the requirement does not inflate the score —
    a 10-year candidate and a 6-year candidate both fully satisfy a 5-year
    minimum, which is the correct screening semantics (avoids penalizing the
    adequately-qualified in favor of the most-tenured).

    Args:
        candidate_years: Total years of experience, or None if unknown.
        required_years: JD minimum, or None if unspecified.

    Returns:
        An ExperienceScore in [0, 1] with rationale.
    """
    if required_years is None or required_years <= 0:
        return ExperienceScore(
            score=1.0,
            candidate_years=candidate_years,
            required_years=required_years,
            rationale="No minimum experience specified.",
        )

    if candidate_years is None:
        return ExperienceScore(
            score=0.5,
            candidate_years=None,
            required_years=required_years,
            rationale="Candidate experience could not be determined; neutral score applied.",
        )

    ratio = candidate_years / required_years
    score = min(ratio, 1.0)
    if score >= 1.0:
        rationale = (
            f"{candidate_years:.1f} yrs meets or exceeds the {required_years}-yr minimum."
        )
    else:
        rationale = (
            f"{candidate_years:.1f} yrs is below the {required_years}-yr minimum "
            f"({score:.0%} of requirement)."
        )
    return ExperienceScore(
        score=round(score, 4),
        candidate_years=candidate_years,
        required_years=required_years,
        rationale=rationale,
    )
